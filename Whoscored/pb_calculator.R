### Extract PB Scores from WhoScored

library(RSelenium)
library(stringr)

function(string){ 
  str_extract(string, "\\-*\\d+\\.*\\d*")
}

#CALL SEPARATE FUNCTION FOR HOME AND AWAY TEAM
rD <- rsDriver(browser=c("firefox"))
remDr <- rD[["client"]]

#Test with Norwich game initially
remDr$navigate("https://www.whoscored.com/Matches/1315021/LiveStatistics/Argentina-Primera-División-2018-2019-Boca-Juniors-Banfield")
Sys.sleep(2)

HA <- "away" #this will be in function call

#Get teams names
teams <- remDr$findElements(using='xpath', value="//div[@id='match-header']//*[@class='team-link ']")
home <- teams[[1]]$getElementText()
away <- teams[[2]]$getElementText()
result <- remDr$findElements(using='xpath', value="//div[@id='match-header']//*[@class='result']")[[1]]$getElementText()
homeGoals <- as.integer(substr(result, 1, 1))
awayGoals <- as.integer(substr(result, nchar(result), nchar(result)))

homeDF <- data.frame(player = as.character(), 
                             team = as.character(),
                             teamGoals = as.integer(),
                             homeaway = as.integer(),
                             age = as.integer(),
                             position = as.character(),
                             player_id = as.integer(),
                             shots = as.integer(),
                             shotsOT = as.integer(),
                             keyPasses = as.integer(),
                             dribbles = as.integer(),
                             fouled = as.integer(),
                             offsides = as.integer(),
                             disp = as.integer(),
                             unsTouches = as.integer(),
                             totalTackles = as.integer(),
                             interceptions = as.integer(),
                             clearances = as.integer(),
                             blockedShots = as.integer(),
                             fouls = as.integer(),
                             passes = as.integer(),
                             passAccuracy = as.integer(),
                             crosses = as.integer(),
                             accCrosses = as.integer(),
                             longBalls = as.integer(),
                             accLongBalls = as.integer(),
                             throughBalls = as.integer(),
                             accThroughBalls = as.integer(),
                             rating = as.integer(),
                             stringsAsFactors = F)


#CLICK OFFENSIVE FOR BOTH TEAMS
offensiveHomeElem <- remDr$findElements(using='css', "[href='#live-player-home-offensive']")
offensiveHomeElem[[1]]$clickElement()
offensiveAwayElem <- remDr$findElements(using='css', "[href='#live-player-away-offensive']")
offensiveAwayElem[[1]]$clickElement()
Sys.sleep(2)

#find offensive stats and player name elements
playerElem <- remDr$findElements(using = 'xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='player-link']")
shotsElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='ShotsTotal ']")
shotsOTElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='ShotOnTarget ']")
keyPassElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='KeyPassTotal ']")
dribbleElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='DribbleWon ']")
fouledElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='FoulGiven ']")
offsidesElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='OffsideGiven ']")
dispElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='Dispossessed ']")
unsTouchesElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='Turnover ']")
ratingElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='rating ']")

#Get player positions and age
metaElem <- remDr$findElements(using = 'xpath', value="//div[@id='statistics-table-home-offensive']//*[@class='pn']")

#Add player name and offensive stats to dataframe
for (i in 1:length(playerElem)) {
  homeDF[i, "player"] <- gsub(" \\(.*?\\)", "", playerElem[[i]]$getElementText()[[1]])
  # if (grepl("\\()", playername) {
  #   homeDF[i, "player"] <- substr(playername, 1, unlist(str_locate(playername, "\\("))[1]-2)
  # } else {
  #   homeDF[i, "player"] <- playername
  # }
  playerHTML <- playerElem[[i]]$getElementAttribute("outerHTML")
  PID <- numextract(playerHTML)
  metaString <- metaElem[[i+1]]$getElementText()
  age <- substr(metaString, unlist(str_locate(metaString, "\n"))[1]+1, unlist(str_locate(metaString, "\n"))[1]+2)
  position <- substr(metaString, unlist(str_locate(metaString, ","))[1]+2, nchar(metaString))
  homeDF[i, "age"] <- age
  homeDF[i, "position"] <- position
  homeDF[i, "player_id"] <- PID
  homeDF[i,"shots"] <- shotsElem[[i]]$getElementText()
  homeDF[i,"shotsOT"] <- shotsOTElem[[i]]$getElementText()
  homeDF[i,"keyPasses"] <- keyPassElem[[i]]$getElementText()
  homeDF[i,"rating"] <- ratingElem[[i]]$getElementText()
  homeDF[i,"dribbles"] <- dribbleElem[[i]]$getElementText()
  homeDF[i,"fouled"] <- fouledElem[[i]]$getElementText()
  homeDF[i,"offsides"] <- offsidesElem[[i]]$getElementText()
  homeDF[i,"disp"] <- dispElem[[i]]$getElementText()
  homeDF[i,"unsTouches"] <- unsTouchesElem[[i]]$getElementText()
}

#Input player team, teamGoals and homeaway

homeDF$team <- home[[1]]
homeDF$teamGoals <- homeGoals
homeDF$homeaway <- "H"

#CLICK DEFENSIVE FOR BOTH TEAMS
defensiveHomeElem <- remDr$findElements(using='css', "[href='#live-player-home-defensive']")
defensiveHomeElem[[1]]$clickElement()
defensiveAwayElem <- remDr$findElements(using='css', "[href='#live-player-away-defensive']")
defensiveAwayElem[[1]]$clickElement()
Sys.sleep(2)

totalTacklesElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-defensive']//*[@class='TackleWonTotal ']")
interceptionsElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-defensive']//*[@class='InterceptionAll ']")
clearancesElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-defensive']//*[@class='ClearanceTotal ']")
blockedShotsElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-defensive']//*[@class='ShotBlocked ']")
foulsElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-defensive']//*[@class='FoulCommitted ']")

#add defensive stats to home dataframe
for (i in 1:length(totalTacklesElem)) {
  homeDF[i,"totalTackles"] <- totalTacklesElem[[i]]$getElementText()
  homeDF[i,"interceptions"] <- interceptionsElem[[i]]$getElementText()
  homeDF[i,"clearances"] <- clearancesElem[[i]]$getElementText()
  homeDF[i,"blockedShots"] <- blockedShotsElem[[i]]$getElementText()
  homeDF[i,"fouls"] <- foulsElem[[i]]$getElementText()
}

#CLICK PASSING FOR BOTH TEAMS
passingHomeElem <- remDr$findElements(using='css', "[href='#live-player-home-passing']")
passingHomeElem[[1]]$clickElement()
passingAwayElem <- remDr$findElements(using='css', "[href='#live-player-away-passing']")
passingAwayElem[[1]]$clickElement()
#Sys.sleep(2)

totalPassesElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-passing']//*[@class='TotalPasses ']")
passAccuracyElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-passing']//*[@class='PassSuccessInMatch ']")
crossesElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-passing']//*[@class='PassCrossTotal ']")
accCrossesElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-passing']//*[@class='PassCrossAccurate ']")
longBallsElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-passing']//*[@class='PassLongBallTotal ']")
accLongBallsElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-passing']//*[@class='PassLongBallAccurate ']")
throughBallsElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-passing']//*[@class='PassThroughBallTotal ']")
accThroughBallsElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-passing']//*[@class='PassThroughBallAccurate ']")

for (i in 1:length(totalPassesElem)) {
  homeDF[i,"passes"] <- totalPassesElem[[i]]$getElementText()
  homeDF[i,"crosses"] <- crossesElem[[i]]$getElementText()
  homeDF[i,"accCrosses"] <- accCrossesElem[[i]]$getElementText()
  homeDF[i,"longBalls"] <- longBallsElem[[i]]$getElementText()
  homeDF[i,"accLongBalls"] <- accLongBallsElem[[i]]$getElementText()
  homeDF[i,"throughBalls"] <- throughBallsElem[[i]]$getElementText()
  homeDF[i,"accThroughBalls"] <- accThroughBallsElem[[i]]$getElementText()
  homeDF[i,"passAccuracy"] <- passAccuracyElem[[i]]$getElementText()
}

#remove players that didnt play in game
homeDF[homeDF=="-"] <- NA
homeDF <- homeDF[complete.cases(homeDF), ]

homeDF$goals <- 0
homeDF$assists <- 0
homeDF$yellow <- 0
homeDF$red <- 0
homeDF$mins <- 90
homeDF$owngoal <- 0
homeDF$penscored <- 0
homeDF$penmissed <- 0
homeDF$keeperpensaved <- 0
homeDF$lastmantackle <- 0

#Messing around with incident data
#Home team incident data
incidentsHome <- data.frame(incident=as.character(), stringsAsFactors = F)
#identify incident icons
incidentHomeElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-home-passing']//*[@class='incident-icon']")
#loop through all incidents
for(i in 1:length(incidentHomeElem)) {
  incidentHTML <- incidentHomeElem[[i]]$getElementAttribute("outerHTML")
  PID <- incidentHomeElem[[i]]$getElementAttribute("data-player-id")
  minute <- incidentHomeElem[[i]]$getElementAttribute("data-minute")
  second <- incidentHomeElem[[i]]$getElementAttribute("data-second")
  #Find type of incident
  if(grepl("goalnormal", incidentHTML) | grepl("penaltyscored", incidentHTML)) {
    #remember to add column of pen conceded (may need to write separate if)
    homeDF[which(homeDF$player_id == PID), "goals"] <-  homeDF[which(homeDF$player_id == PID), "goals"] + 1
  } else if(grepl("yellowcard", incidentHTML)) {
    homeDF[which(homeDF$player_id == PID), "yellow"] <-  homeDF[which(homeDF$player_id == PID), "yellow"] + 1
  } else if(grepl("redcard", incidentHTML) | grepl("secondyellow", incidentHTML)) {
    homeDF[which(homeDF$player_id == PID), "red"] <-  homeDF[which(homeDF$player_id == PID), "red"] + 1
  } else if(grepl("assist", incidentHTML)) {
    homeDF[which(homeDF$player_id == PID), "assists"] <-  homeDF[which(homeDF$player_id == PID), "assists"] + 1
  } else if(grepl("goalown", incidentHTML)) {
    homeDF[which(homeDF$player_id == PID), "goalown"] <-  homeDF[which(homeDF$player_id == PID), "goalown"] + 1
  } else if(grepl("penaltymissed", incidentHTML)) {
    homeDF[which(homeDF$player_id == PID), "penmissed"] <-  homeDF[which(homeDF$player_id == PID), "penmissed"] + 1
  } else if(grepl("keeperpenaltysaved", incidentHTML)) {
    homeDF[which(homeDF$player_id == PID), "keeperpensaved"] <-  homeDF[which(homeDF$player_id == PID), "keeperpensaved"] + 1
  } else if(grepl("lastmantackle", incidentHTML)) {
    homeDF[which(homeDF$player_id == PID), "lastmantackle"] <-  homeDF[which(homeDF$player_id == PID), "lastmantackle"] + 1
  } else if(grepl("suboff", incidentHTML)) {
    if(minute <= 90) { 
      homeDF[which(homeDF$player_id == PID), "mins"] <- as.integer(minute)
    } else {
      homeDF[which(homeDF$player_id == PID), "mins"] <- 90
    }
  } else if(grepl("subon", incidentHTML)) {
      if(minute <= 90) { 
        homeDF[which(homeDF$player_id == PID), "mins"] <- 90 - as.integer(minute)
      } else {
        homeDF[which(homeDF$player_id == PID), "mins"] <- 0
      }
  }
}

#Calculate PB
homeDF$pb <- 0




# 
# #Away team incident data
# incidentsAway <- data.frame(incident=as.character(), stringsAsFactors = F)
# #USE SIMILAR XPATH FOR PLAYER STATS????
# incidentAwayElem <- remDr$findElements(using='xpath', value="//div[@id='statistics-table-away-summary']//*[@class='incident-icon']")
# for(i in 1:length(incidentAwayElem)) {
#   incidentsAway[i,1] <- incidentAwayElem[[i]]$getElementAttribute("outerHTML")
# }
# 
# incidentAwayElem[[1]]$getElementAttribute("data-minute") #minute of 1st event
# incidentAwayElem[[1]]$getElementAttribute("data-second") #second of event
# incidentAwayElem[[1]]$getElementAttribute("data-player-id") #player id
# incidentAwayElem[[1]]$getElementAttribute("data-team-id") #team id
# grepl("clearanceofftheline", incidentsAway[1,1]) #test if incident 1 was a clearance off the line

remDr$close()
rD[["server"]]$stop() 

