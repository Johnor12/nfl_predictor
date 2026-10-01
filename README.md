# nfl_predictor

the goal of this project is to build a system for predicting what happens during an NFL season; specifically, it attempts to predict the result of each snap for the season from an offensive perspective, including which players were on the field and the outcomes for those players (rushing yards, receiving yards, passes, receptions, first downs, touchdowns (including who gets credit), field goals, fumbles, interceptions, and penalty yards). 

Specifically in scope: injuries (both when they occur and how long they sideline a player for), coaching personnel changes, roster changes (including trades), weather (simplistic model based on averages for location and time), penalties (including yardage and ejections if relevant), kickoff returns, coach speak and natural language interpretation of headlines.

Specifically out of scope: between season events

Data requirements:
1. at minimum, inputs (teams, scores, location, weather, coaching staff, players, referees, injuries etc) and outputs (outcomes listed above) for as many NFL snaps as possible
2. supplemental information: historical logs of headlines

separate predictors for different questions:

the system could still have value without complete data coverage.