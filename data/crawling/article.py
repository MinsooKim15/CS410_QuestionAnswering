
import hashlib
HASH_NAME = "md5"
class Article():
    def __init__(self,id, category, userName,userType, content, title, inLinkId ="", replyList = [], likeCount = 0, commentCount = 0, viewCount = 0, uniqueViewCount=0):
        self.id = id
        self.category = category
        self.userName = userName
        self.userType = userType
        self.content = content
        self.title = title
        self.inLinkId = inLinkId
        self.replyList = replyList
        self.likeCount = likeCount
        self.commentCount = commentCount
        self.viewCount = viewCount
        self.uniqueViewCount = uniqueViewCount
    @staticmethod
    def fromCrawl(id, category, userName, userType, content, title, inLinkId ="", replyList = [], likeCount = 0, commentCount = 0, viewCount = 0, uniqueViewCount=0):

        new_id = ""
        if category == "post":
            new_id = "post_" + str(id)
        else:
            new_id = "script_"+ str(id)
        article = Article(
            id=new_id,
            category=category,
            userName=userName,
            userType=userType,
            content=content,
            title=title,
            inLinkId=inLinkId,
            replyList=replyList,
            likeCount=likeCount,
            commentCount=commentCount,
            viewCount=viewCount,
            uniqueViewCount=uniqueViewCount
        )
        return article
    @staticmethod
    def fromDict(source):
        replyList = []
        for item in source[u"replyList"]:
            replyList.append(Reply.fromDict(item))
        article = Article(
            id = source[u"id"],
            category = source[u"category"],
            userName = source[u"userName"],
            userType = source[u"userType"],
            content = source[u"content"],
            title = source[u"title"],
            inLinkId = source[u"inLinkId"],
            replyList = replyList,
            likeCount = source[u"likeCount"],
            commentCount= source[u"commentCount"],
            viewCount = source[u"viewCount"],
            uniqueViewCount= source[u"uniqueViewCount"]
        )
        return article
    def toDict(self):
        replyDictList = []
        for item in self.replyList:
            replyDictList.append(item.toDict())
        dict = {
            u"id":self.id,
            u"category" : self.category,
            u"userName" : self.userName,
            u"userType" : self.userType,
            u"content" : self.content,
            u"title" : self.title,
            u"inLinkId": self.inLinkId,
            u"replyList" : replyDictList,
            u"likeCount" : self.likeCount,
            u"commentCount" : self.commentCount,
            u"viewCount" : self.viewCount,
            u"uniqueViewCount" : self.uniqueViewCount
        }
        return dict

    def getTextIdPair(self):
        textResult = self.title + " " + self.content
        replyResult = ""
        for item in self.replyList:
            replyResult = replyResult + " " + item.getText
            textResult = textResult + " " + replyResult
        return (textResult, self.id)
class Reply():
    def __init__(self, id, userName, userType, content, inLinkId,upvote=0,replyType=0,subReplyList=[]):
        self.id = id
        self.userName = userName
        self.userType = userType
        self.content = content
        self.inLinkId = inLinkId
        self.upvote = upvote
        self.replyType = replyType
        self.subReplyList = subReplyList
    @staticmethod
    def fromCrawl(userName, userType, content, inLinkId="",upvote=0,replyType=0,subReplyList=[]):
        # hash id stuff
        stringCon = ""
        userName = str(userName)
        content = str(content)
        if len(content) > 3:
            stringCon = content[:3]
        else:
            stringCon = content
        txt = userName + " " + stringCon
        text = txt.encode('utf-8')
        md5 = hashlib.new(HASH_NAME)

        md5.update(text)
        result = md5.hexdigest()
        id  = result
        # hash id finish

        reply = Reply(
            id=id,
            userName=userName,
            userType=userType,
            content=content,
            inLinkId=inLinkId,
            upvote=upvote,
            replyType=replyType,
            subReplyList=subReplyList
        )
        return reply
    @staticmethod
    def fromDict(source):
        upvote = 0
        if "upvote" in source:
            upvote = source[u"upvote"]
        subReplyList = []
        for item in source[u"subReplyList"]:
            subReplyList.append(Reply.fromDict(item))
        reply = Reply(
            id = source["id"],
            userName = source["userName"],
            userType = source["userType"],
            content = source["content"],
            inLinkId= source["inLinkId"],
            upvote= upvote,
            replyType = source["replyType"],
            subReplyList= subReplyList
        )
        return reply
    def toDict(self):
        subReplyDictList = []
        for subReply in self.subReplyList:
            subReplyDictList.append(subReply.toDict())
        dict = {
            u"id" : self.id,
            u"userName" : self.userName,
            u"userType" : self.userType,
            u"content" : self.content,
            u"inLinkId" : self.inLinkId,
            u"upvote" : self.upvote,
            u"replyType" : self.replyType,
            u"subReplyList": subReplyDictList
        }
        return dict

    def getText(self):
        text = self.content
        for item in self.subReplyList:
            text = text + " " + item.text
        return text