# Reccommitment Drive Tools October 2022

## Purpose

These tools were created to be used along side the weekly membership list uploads to create phonebank membership lists. For full info on the campaign check [here](https://drive.google.com/drive/folders/1wwvvqAfuJR1fDr5zZlp-pVxFz4Cmlq3a?usp=share_link).

If another reccommitment drive occurs these tools can be reused or modified to fit that campaign.

## Scripts

`processNewMembers-reccommit.py` - Similar to processNewMembers.py for the weekly membership list uploads but will also process a new phone bank list.

`reccommitDriveHatCheck.py` - Takes in stats for volunteer tracking and prints consolidated volunteer stats.

`reccommitDriveStats.py` - Takes in calls and colunteer tracking and prints overall drive stats

`ReccommitUtils.py` - Various utility functions.

`reccommitProcessPhoneCallList.py` - Takes a phone bank list that has been used in a phone bank and outputs the various tracking rows.

## Outputs

Note that none of the scripts take output paths as arguments at this time. They have hardcoded output paths to the recommit directory. These paths can be found in `ReccommitUtils.py`. 