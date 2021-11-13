# CourseProject

Please fork this repository and paste the github link of your fork on Microsoft CMT. Detailed instructions are on Coursera under Week 1: Course Project Overview/Week 9 Activities.
 
### base sentence embedding model  
  - 'sentence-transformers/bert-base-nli-mean-tokens'

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
Ta-DahðŸ”®, here are what we found for: assignment
10
>  0(0.65). LiveDataLab Link. I do face same issue. : Hold tight guys! We're aware that the MP links to LiveDataLabs don't work yet. Please check again on Monday! we're working on it.
>  1(0.46). Week 1 Project Overview + Tech. Review Readings Locked?. It is available now.. : We are still working on those pages and will make them available soon. There  is no task from either the Course Project or the Tech Review due any time soon, so please don't worry about missing any important information. In general, please ignore any pages that are not visible to you at this point.
>  2(0.46). Coursera. Try
https://www.coursera.org/learn/cs-410/home/welcome : I can see that about 176 students have not yet been enrolled on Coursera. I'll see what's going on. Even if you're in the "on-campus" session of the class, you should still have access to the same Coursera session as everybody else.
>  3(0.39). Hello!. Hey David, I would love to be a part of your group : I am more than glad to team up with you for the final project David!!
>  4(0.36). Can't find onboarding course. Log in to coursera organization account (UIUC) and you should see it under My courses : It turns out my account was not linked yet, but MCS helped resend the link to do so.
```
