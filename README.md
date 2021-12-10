# CourseProject

Please fork this repository and paste the github link of your fork on Microsoft CMT. Detailed instructions are on Coursera under Week 1: Course Project Overview/Week 9 Activities.
 
- 📼 Presentation Video : https://uillinoisedu-my.sharepoint.com/:v:/g/personal/minsoo4_illinois_edu/EVJ8dtvsoYBDmAu_Wwm6xJcB_8VnBYiwmUtRsuyxzrycpg?e=ctzBOq
 
### requirement

```
python 3.8 
pip install -r requirement.txt
```

### base sentence embedding model  
  - bert-base-nli-mean-tokens(https://huggingface.co/sentence-transformers/bert-base-nli-mean-tokens)
  - all-mpnet-base-v2(https://huggingface.co/sentence-transformers/all-mpnet-base-v2) --> implemented model


### Indexing
![](index.svg)


### Search
#### With REST API
#### query
![](query.svg)

```
 python app.py -t query
data/crawling/example.json
     Preprocess@34012[L]:ready and listening
SentenceSplitter@34012[L]:ready and listening
 SentenceKoBART@34012[L]:ready and listening
  DocVecIndexer@34012[L]:ready and listening
  KeyValIndexer@34012[L]:ready and listening
        gateway@34012[L]:ready and listening
           Flow@34012[I]:🎉 Flow is ready to use!
        🔗 Protocol:            GRPC
        🏠 Local access:        0.0.0.0:60808
        🔒 Private network:     192.168.35.52:60808
Please type a sentence: assignment
search from DocVectorIndexer
Ta-DahðŸ”®, here are what we found for: unable to find onboarding course
10
>  0(0.51). TA Office hours-21st August. Same here, I'm unable to join as well. : Below is the reply from MCS Support
"My apologies. TA Office Hours don't start until next week (first week of class). The Live Event you're referring to was created by mistake and has been deleted since. Sorry for the confusion."
>  1(0.50). Can't find onboarding course. Log in to coursera organization account (UIUC) and you should see it under My courses : It turns out my account was not linked yet, but MCS helped resend the link to do so.
>  2(0.38). Conditional Entropy. I figured it out: I believe the Conditional Entropy slide is incorrect: the example conditional entropy calculation on this slide does not agree with the formula on the next slide. In other words, the log of each conditional probability needs to be multiplied by the joint probability NOT the conditional probability. (Or you could multiply the log of the conditional probability by the conditional probability and the marginal probability of the conditioning event, but that just seems complicated. : How can the probability of event A occurring be less than the probability of A occurring and B occurring?
I'm not sure but take a look at:
https://brilliant.org/wiki/conditional-probability-distribution/
>  3(0.38). Can't sign up for LiveDataLab. Think this was answered in the #6. They should get it Monday. : LiveDataLab is a complicated cloud-based infrastructure, which we are still working on setting up. We hope to complete the setup ASAP and will post a note here once it's available. You don't need to do anything for now.  LiveDataLab is used for MPs, and the hard deadline for MP1 is sometime in Oct.
>  4(0.37). Any luck or tips for installing Python3.5 on newer MacOS?. I have attempted these steps and am still unable to install and run python on my machine. I hav MacOS Big Sur. Is it possible for me to get help from a TA in office hours? If so, when would be the best time? : Paul, MeTA should work with Python 3.x.... did you try just using the default Python you have? Are you running into trouble installing MeTA then?
```

### demo
http://uiuc-cs410-demo.ngrok.io/(temporary address)
