import requests

class Accessibility4All:
    def __init__(self):
        return None

    def open_license(self, kg_license):
        # Case 1: all elements are '-'
        if all(license == '-' for license in kg_license):
            self.open_license_value = 0
            return self.open_license_value

        # Retrieve the open license list from Open Knowledge Foundation
        url = "https://raw.githubusercontent.com/okfn/licenses/master/licenses/groups/all.json"
        response = requests.get(url)

        if response.status_code == 200:
            open_license_data = response.json()

            # Extract all URLs from the OKFN list
            okfn_urls = {lic["url"] for lic in open_license_data if "url" in lic}

            # At least one KG license matches an open license
            if any(license in okfn_urls for license in kg_license):
                self.open_license_value = 1
            else:
                # Case 3: licenses are present but not recognized as open
                self.open_license_value = 0.5

            return self.open_license_value

        else:
            # Request failed
            return {"error": "Failed to retrieve license information"}