import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium import webdriver
from urllib.request import urlopen
from bs4 import BeautifulSoup as bs
from urllib.parse import quote_plus
from selenium.webdriver.common.keys import Keys
import time
from selenium.common.exceptions import NoSuchElementException
from article import *
import json

# user id and password for selenium log in to campuswire

USER_ID = "minsoo4@illinois.edu"
USER_PASSWORD = "rkdghkeh95"
FILENAME = "data_1125.json"
CHROME_DRIVER_PATH = "/Users/minsookim/Downloads/chromedriver"
MINIMUM_POST_ID = 2
MAXIMUM_POST_ID = 1750
def check_exists_by_selector(driver, xpath):
    try:
        driver.find_element_by_css_selector(xpath)
    except NoSuchElementException:
        return False
    return True



def getSubReplyList(element):
    subReplyResultList = []
    if check_exists_by_selector(element,'.post-comments-list'):
        subReplyList = element.find_element_by_class_name("post-comments-list").find_elements_by_class_name("media")
        if subReplyList != None:
            if len(subReplyList) > 0:
                for subItem in subReplyList:
                    # print("useName")
                    # print(subItem.find_element_by_class_name("user--name").find_element_by_tag_name("h6").text)
                    userName = subItem.find_element_by_class_name("user--name").find_element_by_tag_name("h6").text
                    userType = 2
                    # print("userType")
                    if check_exists_by_selector(element,'.ta-badge'):
                        userType = 1
                    if check_exists_by_selector(element,'.instructor-badge'):
                        userType = 0
                    # print("본문")
                    # print(subItem.find_element_by_class_name("text-wrapper").text)
                    content = subItem.find_element_by_class_name("text-wrapper").text
                    subReplyList = getSubReplyList(subItem)
                    reply = Reply.fromCrawl(
                        userName = userName,
                        userType = userType,
                        content = content,
                        subReplyList = subReplyList,
                        replyType = 1
                    )
                    subReplyResultList.append(reply)
    return subReplyResultList



def getPostItem(id, driver):
    postUserName = driver.find_element_by_class_name("user--name").find_element_by_tag_name("h6").text
    postUserType = 2

    if check_exists_by_selector(driver, '.ta-badge'):
        postUserType = 1
    if check_exists_by_selector(driver, '.instructor-badge'):
        postUserType = 0
    title = driver.find_element_by_class_name("post-view").find_element_by_class_name("post-title").find_element_by_tag_name("h3").text
    postContent = driver.find_element_by_class_name("post-view").find_element_by_class_name("post-body").text
    likeCount = driver.find_element_by_class_name("post-view").find_element_by_class_name("post-like").find_element_by_class_name("counter").text
    commentCount = driver.find_element_by_class_name("post-view").find_element_by_class_name("post-comments-count").find_element_by_tag_name("span").text
    viewCount = driver.find_element_by_class_name("post-view").find_element_by_class_name("post-views-count").find_element_by_tag_name("span").text
    uniqueViewCount = driver.find_element_by_class_name("post-view").find_element_by_class_name("unique-views-count-wrap").find_element_by_tag_name("span").text
    topAnswerList = driver.find_elements_by_class_name("top-answer")
    replyList = []
    for item in topAnswerList:
        # print("userName")
        # print(item.find_element_by_class_name("user--name").find_element_by_tag_name("h6").text)
        replyUserName = item.find_element_by_class_name("user--name").find_element_by_tag_name("h6").text
        replyUserType = 2
        if check_exists_by_selector(driver, '.ta-badge'):
            replyUserType = 1
        if check_exists_by_selector(driver, '.instructor-badge'):
            replyUserType = 0
        upvote = int(item.find_element_by_class_name("vote-counter").find_element_by_class_name("badge").text)
        replyContent = item.find_element_by_class_name("post-body").text
        subReplyList = getSubReplyList(item)
        reply = Reply.fromCrawl(
            userName= replyUserName,
            userType= replyUserType,
            content= replyContent,
            subReplyList=subReplyList,
            replyType=0
        )
        replyList.append(reply)
    article = Article.fromCrawl(
        id = id,
        category = "post",
        userName = postUserName,
        userType = postUserType,
        content = postContent,
        title = title,
        inLinkId = "",
        replyList =replyList,
        likeCount = likeCount,
        commentCount = commentCount,
        viewCount = viewCount,
        uniqueViewCount=uniqueViewCount
    )
    return article

def crawl_caampuswire():
    # 브라우저 설정 및 호출
    url = 'https://campuswire.com/signin'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(CHROME_DRIVER_PATH, chrome_options=chrome_options)
    driver.get(url)
    # 로그인 후 화면 전환 대기
    body = driver.find_elements_by_class_name("form-control")
    body[0].send_keys(USER_ID)
    body[1].send_keys(USER_PASSWORD)
    driver.find_element_by_class_name("btn").click()
    time.sleep(3)
    # 로그인 완료 후 피드 이동
    base_url = "https://campuswire.com/c/G0A3AA370/feed/"
    articleList = []
    for i in range(MINIMUM_POST_ID, MAXIMUM_POST_ID):
        url = base_url + str(i)
        driver.get(url)
        time.sleep(3)
        if check_exists_by_selector(driver, ".post-body"):
            article = getPostItem(i, driver)
            articleList.append(article)
    jsonList = []
    for article in articleList:
        jsonList.append(article.toDict())
    with open(FILENAME, 'w', encoding="utf-8") as f:
        json.dump(jsonList, f, ensure_ascii=False)

if __name__ == "__main__":
    crawl_caampuswire()