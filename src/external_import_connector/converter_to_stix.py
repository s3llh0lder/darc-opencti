import stix2
from pycti import Identity


class ConverterToStix:
    def __init__(self, helper):
        self.helper = helper
        self.author = self.create_author()

    def create_author(self):
        return stix2.Identity(
            id=Identity.generate_id(
                name="Dark Web Crawler", identity_class="organization"
            ),
            name="Dark Web Crawler",
            identity_class="organization",
            description="Data collected from dark web sources.",
        )

    def create_obs(self, url):
        """Convert URL to STIX Observable"""
        return stix2.URL(value=url, created_by_ref=self.author["id"])
