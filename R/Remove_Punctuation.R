library(dplyr)
library(stringr)
library(openxlsx)
library(tools)
library(stringr)

z = choose.dir()
wd = setwd(z)

a=file.choose()
y = read.xlsx(a)


# Delete unwanted space;
?gsub
for(i in dCol){
  temp[[i]] = gsub("[[:space:]]","",temp[[i]])
}

# Delete unwanted period
for(i in dCol){
  temp[[i]] = gsub("\\.", "", temp[[i]])
}

# Delete unwanted numeric characters
for(i in dCol){
  # Delete numueric characters
  temp[[i]] = gsub("[0-9]+", "", temp[[i]])
}

# First Letter to Capital
for(i in dCol){
  # Delete numueric characters
  temp[[i]] = str_to_title(temp[[i]])
}

# to Upper case letter
for(i in dCol){
  temp[[i]] = toupper(temp[[i]])
}

# Convert to numeric column
for(i in dCol){
  temp[[i]] = as.numeric(temp[[i]])
}

# Delete Punctuation "*", "**", "\n", white space before 1st letter and after the last letter
for(i in dCol){
  temp[[i]] = gsub("[*]","",temp[[i]])
  #temp[[i]] = gsub("\n","",temp[[i]])
  temp[[i]] = gsub("^\\s+|\\s+$", "",temp[[i]])
  
}


# Export
write.xlsx(temp,paste(basename(a),"_fixed.xlsx",sep = ""))


rem_id = which(is.na(temp$LotID))
temp = temp[-rem_id,]
str(temp)


head(temp)
unique(temp$Municipality)
unique(temp$Barangay)
sort(unique(temp$UTILITY.COMPANY))
write.xlsx(sort(unique(temp$UTILITY.COMPANY)),"x_utilityCompany.xlsx",row.names=FALSE)


str(temp)
unique(temp$Priority)
