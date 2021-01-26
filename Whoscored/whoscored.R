#### FIND WHOSCORED RATINGS FOR ALL PLAYERS IN TOP 5 LEAGUES
##look in terminal to change collection of data - add goal, assists etc too

library(RSelenium)

rD <- rsDriver(browser=c("firefox"))
remDr <- rD[["client"]]

remDr$navigate("https://www.whoscored.com/Matches/1290287/Live/England-Championship-2018-2019-Middlesbrough-Norwich")

#CLICK ENTER WEBSITE

minappsElem <- remDr$findElements(using = 'css', "[data-backbone-model-attribute='isMinApp']")
minappsElem[[2]]$clickElement()

whoscored <- data.frame(player_name = as.character(), 
                        rating=as.double(),
                        stringsAsFactors = FALSE)

current_page_ratings <- data.frame(player_name = as.character(), 
                                   rating=as.double(),
                                   stringsAsFactors = FALSE)

#find number of pages to loop through
numpages <- remDr$findElements(using = 'xpath', "//*[@id='statistics-paging-summary']/div/dl[2]/dt/b")
numpages_string <- numpages[[1]]$getElementText()[[1]]
u <- gregexpr(numpages_string, pattern ='/')[[1]][1]
pages_whoscored <- as.integer(str_sub(numpages_string, u+1, u+3))

for (j in 1:pages_whoscored) {
  
  lastnumElem <- remDr$findElements(using = 'css', "[class='pn']")
  num_of_players <- length(lastnumElem) - 1
  
  for (i in 1:num_of_players) {
    #PLAYERS
    playerElem <- remDr$findElements(using = 'css', "[class='player-link']")
    cur_player <- playerElem[[i]]$getElementText() #each int corresponds to one of 10 players on page
    
    #RATINGS
    path <- paste("//*[@id='player-table-statistics-body']/tr[", i, "]/td[14]", sep="")
    ratingElem <- remDr$findElements(using = 'xpath', path)
    cur_rat <- ratingElem[[1]]$getElementText()
    
    current_page_ratings[i, "player_name"] <- cur_player
    current_page_ratings[i, "rating"] <- as.double(cur_rat[[1]])
  }
  
  whoscored <- rbind(whoscored, current_page_ratings)
  
  #press next
  nextElem <- remDr$findElements(using = 'css', "[id='next']") #find next button
  nextElem[[2]]$clickElement() #click next
  Sys.sleep(5)

}



#remove duplicates
whoscored <- whoscored[!duplicated(whoscored$player_name), ]


