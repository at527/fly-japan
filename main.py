from dataclasses import dataclass
from datetime import date, datetime
import json
import config
import requests
import concurrent.futures
import time
import csv


@dataclass
class FlightItinerary:
    home_out: str
    dest_in: str
    dest_out: str
    home_in: str
    date_from: date
    date_to: date


@dataclass
class KiwiFlightInfo:
    price: int
    duration: float
    quality: float
    link: str


@dataclass
class BestFlights:
    flight_plan: FlightItinerary
    search_results: list[KiwiFlightInfo]

    def date_to_kiwi_format(self, d: date) -> str:
        return d.strftime("%d/%m/%Y")

    def get_raw_kiwi_results(self, flight_plan) -> list[dict]:
        """Returns the top 5 flight plans json responses from kiwi"""

        url = "https://api.tequila.kiwi.com/v2/flights_multi"
        payload = {
            "requests": [
                {
                    "limit": 5,
                    "sort": "quality",
                    "curr": "USD",
                    "fly_to": flight_plan.dest_in,
                    "fly_from": flight_plan.home_out,
                    "date_from": self.date_to_kiwi_format(flight_plan.date_from),
                    "date_to": self.date_to_kiwi_format(flight_plan.date_from),
                    "adults": 1,
                },
                {
                    "limit": 5,
                    "sort": "quality",
                    "curr": "USD",
                    "fly_to": flight_plan.home_in,
                    "fly_from": flight_plan.dest_out,
                    "date_from": self.date_to_kiwi_format(flight_plan.date_to),
                    "date_to": self.date_to_kiwi_format(flight_plan.date_to),
                    "adults": 1,
                },
            ],
        }

        json_payload = json.dumps(payload)

        headers = {
            "Content-Type": "application/json",
            "apikey": config.kiwi_multi_city_key,
        }

        try:
            response = requests.post(url, data=json_payload, headers=headers)
            response.raise_for_status()  # Raise an exception if the response status code is not 2xx

            response_data = json.loads(response.text)

            return response_data

        except Exception as e:
            print("Error: ", e)
        return None

    def extract_flight_info(self, kiwi_result: dict) -> KiwiFlightInfo:
        price: int = kiwi_result["price"]
        duration: float = round((kiwi_result["duration"]) / 3600, 2)
        quality: float = kiwi_result["quality"]
        link: str = kiwi_result["deep_link"]

        return KiwiFlightInfo(price, duration, quality, link)

    def set_flights(self, kiwi_result: dict):
        self.search_results = [self.extract_flight_info(i) for i in kiwi_result]

    def search_and_set_flights(self) -> bool:
        try:
            print("Searching: ", self.flight_plan)
            raw_top_5_itineraries = self.get_raw_kiwi_results(self.flight_plan)
            self.set_flights(raw_top_5_itineraries)
            return True

        except Exception as e:
            print("Error: ", e)

        return None


@dataclass
class AllOptionsForJapan:
    all_flight_plans: list[BestFlights]

    def search_and_set_best_flights(self):
        max_concurrent = 2
        # Create a ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_concurrent
        ) as executor:
            # Use executor.map to run get_best_flights concurrently for each flight
            futures = [
                executor.submit(f.search_and_set_flights) for f in self.all_flight_plans
            ]

            # Retrieve results as they complete
            for future in concurrent.futures.as_completed(futures):
                time.sleep(2.2)

    def to_csv(self, csv_name):
        # Define the CSV file's header
        csv_header = [
            "Home Out",
            "Dest In",
            "Dest Out",
            "Home In",
            "Date From",
            "Date To",
            "Price",
            "Duration",
            "Quality",
            "Link",
        ]

        # Write FlightInfo objects to the CSV file
        with open(csv_name, mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(csv_header)

            # Use a list comprehension to generate rows
            rows = [
                [
                    flight_plan.home_out,
                    flight_plan.dest_in,
                    flight_plan.dest_out,
                    flight_plan.home_in,
                    flight_plan.date_from,
                    flight_plan.date_to,
                    flight_info.price,
                    flight_info.duration,
                    flight_info.quality,
                    flight_info.link,
                ]
                for plan in self.all_flight_plans
                for flight_info in plan.search_results
                for flight_plan in [
                    plan.flight_plan
                ]  # Create a list to simplify access
            ]

            # Write the generated rows to the CSV file
            writer.writerows(rows)

        print(f"Flight info has been written to {csv_name}")
        return 0


def all_flight_options(
    us_ports, japan_ports, date_from, date_to
) -> list[FlightItinerary]:
    return [
        FlightItinerary(u_out, j_in, j_out, u_in, date_from, date_to)
        for u_out in us_ports
        for j_in in japan_ports
        for j_out in japan_ports
        for u_in in us_ports
    ]


def curDateTimeStr() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")


def main():
    socal_ports = ["LAX"]
    norcal_ports = ["SFO"]
    japan_ports = ["HND", "NRT", "FUK", "KIX", "NGO", "CTS"]
    # japan_ports = ["NRT"]

    date_from = date(2024, 3, 22)
    date_to = date(2024, 4, 1)

    all_socal_options = all_flight_options(socal_ports, japan_ports, date_from, date_to)
    all_norcal_options = all_flight_options(
        norcal_ports, japan_ports, date_from, date_to
    )

    best_socal_flights = AllOptionsForJapan(
        [BestFlights(f, []) for f in all_socal_options]
    )
    best_norcal_flights = AllOptionsForJapan(
        [BestFlights(f, []) for f in all_norcal_options]
    )

    best_socal_flights.search_and_set_best_flights()
    best_socal_flights.to_csv(f"socal_flights_{curDateTimeStr()}.csv")

    best_norcal_flights.search_and_set_best_flights()
    best_norcal_flights.to_csv(f"norcal_flights_{curDateTimeStr()}.csv")


if __name__ == "__main__":
    main()
