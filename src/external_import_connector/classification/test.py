import json

from src.external_import_connector.classification.v2.classifier import DataClassifierV2
from src.external_import_connector.classification.v3.classifier import DataClassifierV3
from src.external_import_connector.classification.v3_1.classifier import (
    DataClassifierV31,
)
from src.external_import_connector.classification.v3_2.classifier import (
    DataClassifierV32,
)

if __name__ == "__main__":

    # Initialize classifier
    classifier = DataClassifierV2()
    classifier2 = DataClassifierV3()
    classifier3 = DataClassifierV31()
    classifier32 = DataClassifierV32()

    # Example data to classify
    example_data = "us Register Now New posts Search forums Menu Log in Register Install the app Install Your JavaScript is Disabled Some Forum functions may NOT work properly. Enable JavaScript in your Browser to use all the Forum features. You are using an out of date browser. It may not display this or other websites correctly. You should upgrade or use an alternative browser . [2023 HQ] Leaked $250 PER DAY WITH SIMPLE ADSENSE METHOD - NO WEBSITE NEEDED [WORTH $$$$] Thread starter Mr.Robot Start date September 2, 2024 Tags adsense google method needed website Tagged users None Forums White Hat & Gray Hat Freebies Section White Hat / Gray Hat Money Making Courses & Methods [2023 HQ] Leaked $250 PER DAY WITH SIMPLE ADSENSE METHOD - NO WEBSITE NEEDED [WORTH $$$$] Prev 1 Go to page Go 14 15 16 17 18 Go to page Go 24 Next First Prev 16 of 24 Go to page Go Next Last More options Ignore thread in statistics darkdice90 Member Joined September 2, 2024 Messages 9 Reaction score 0 Points 1 September 2, 2024 #301 zeroday ovaldiamond Member Joined September 2, 2024 Messages 25 Reaction score 2 Points 3 September 4, 2024 #302 w Botishere Advanced Member Joined June 13, 2024 Messages 144 Reaction score 10 Points 18 September 5, 2024 #303 h Mr.Robot said: Sales page [SELL] $249 Per Day With My Simple Google AdSense Method - No Website Needed No Software/Bot Needed! No Need To Pay For A Website (Domain Name + Hosting) No Paid Ads (Like Bing or Facebook Ads) 100% Google AdSense Safe & Legal 100% AUTOMATED Payments Set Up Takes Less Than 1 Day Requires Only 25 Min Of Your Daily Time No Investment Required No Cracking / Programming Websites / Specific Skills Required Can Be Done From Anywhere In The World No e-Whorring / Carding / Trading / Cryptos / Dropshipping / e-Commerce / Fiverr / CPA / Adult / Calls Never Shared Before Easily Scalable Admin Approved Requirements : - A computer - An internet connection - A Google AdSense account - And a human brain Yes that's all Mega.nz Download Link : [Hidden content]"
    # example_data = "test {} hack"
    additional_features = {"Language": "English", "Threat Level": "Low"}

    additional_features2 = {
        "Sentiment Score": 1,  # Example encoded value for "Critical"
        "Keyword Count": 1,  # Example encoded value for "English"
        "Obfuscation Level": 1,  # Example encoded value for "Monitoring"
    }

    additional_features32 = {"sentiment": -0.32, "keyword_count": 3, "obfuscation": 12}

    # Classify the example data
    result = classifier.classify_data(example_data, 1, additional_features)
    print("Classifier v2")
    print(json.dumps(result, indent=2))

    # result = classifier2.classify_data(example_data, 1, additional_features2)
    # print('Classifier v3')
    # print(json.dumps(result, indent=2))

    # result = classifier3.classify_data(example_data, 1, additional_features2)
    # print('Classifier v3_1')
    # print(json.dumps(result, indent=2))

    result = classifier32.classify_data(example_data, 1, additional_features32)
    print("Classifier v3_2")
    print(json.dumps(result, indent=2))
