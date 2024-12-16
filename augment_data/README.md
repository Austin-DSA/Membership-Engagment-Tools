# Action Network Membership Data Augmenter

A simple tool to augment membership data with additional fields.

This tool supports the following (at the moment):

* Adding Austin City Counsil district information based on address. This uses the Austin City website. When used alone this will suffer from inaccuracies that we cannot easily detect, so some numbers will be silently wrong.

Potential additions:

* Address correction to improve the quality of addresses to make the above more precise. This would use https://www.geocod.io/. (This is free up to a limited number of requests per day. This limit will almost certainly be enough to keep up with new members or changes, but will not be enough to run the entire membership list in one day. However, paying for the queries is less than 1 cent per row.)
* Adding state and national district information (and [other information as desired](https://www.geocod.io/guides/congressional-data/)). 
