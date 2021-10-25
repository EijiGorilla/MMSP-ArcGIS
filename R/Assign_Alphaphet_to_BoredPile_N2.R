
# This R script assigns unique ID system of Civil team to my bored pile ID 
# This is needed to be able to update the construction status of bored piles in correspondence to Civil Team status table

library(openxlsx)
library(dplyr)
library(stringr)

z = choose.dir()
wd = setwd(z)

a=file.choose()
y = read.xlsx(a)

nrow(y)
str(y)

y$ID2 = ""
y$nLayer = ""

# Extract unique ID I created for myself: only extract L1, R1, ...
y$nLayer[] = str_extract(y$ID, "L1|L2|L3|L4|M1|M2|M3|M4|R1|R2|R3|R4")

# Extract unique values for CP and Pier Numbers
cp = unique(y$CP)
pier = unique(y$PierNumber)

#pier=="P-164SB"
#pier=="P-164SB"
grep("P-262",pier)

##pier[935], "PR7-120ST

# empty data frae
temp = data.frame()

for (i in seq(cp)) {
#  i=4
  y1 = y[y$CP == cp[i],]

  for (j in seq(pier)) {
 #   j=1227
    #y2[,c(1,9,11,12,13)]
    y2 = y1[y1$PierNumber==pier[j],]
    numPier = length(which(y2$Type == 1))
    
    if (numPier == 4) {
      y2$ID2[y2$nLayer == "L2"] = "A"
      y2$ID2[y2$nLayer == "L1"] = "B"
      y2$ID2[y2$nLayer == "R2"] = "C"
      y2$ID2[y2$nLayer == "R1"] = "D"
      
    } else if (pier[j]=="PR7-120ST" | pier[j]=="PR7-120") {
      y2$ID2[y2$nLayer == "L1"] = "C"
      y2$ID2[y2$nLayer == "L2"] = "B"
      y2$ID2[y2$nLayer == "L3"] = "A"
      y2$ID2[y2$nLayer == "R1"] = "F"
      y2$ID2[y2$nLayer == "R2"] = "E"
      y2$ID2[y2$nLayer == "R3"] = "D"
      
    } else if (pier[j]=="P-261" | pier[j]=="P-262" | pier[j]=="P-158" | pier[j]=="P-157") {
      y2$ID2[y2$nLayer == "L3"] = "A"
      y2$ID2[y2$nLayer == "L2"] = "B"
      y2$ID2[y2$nLayer == "L1"] = "C"
      y2$ID2[y2$nLayer == "R3"] = "D"
      y2$ID2[y2$nLayer == "R2"] = "E"
      y2$ID2[y2$nLayer == "R1"] = "F" 
      
      
    } else if (numPier == 6) {
      y2$ID2[y2$nLayer == "L2"] = "A"
      y2$ID2[y2$nLayer == "L1"] = "B"
      y2$ID2[y2$nLayer == "M2"] = "C"
      y2$ID2[y2$nLayer == "M1"] = "D"
      y2$ID2[y2$nLayer == "R2"] = "E"
      y2$ID2[y2$nLayer == "R1"] = "F"
      
    } else if (numPier == 8) { #P416..
      y2$ID2[y2$nLayer == "L2"] = "A"
      y2$ID2[y2$nLayer == "L1"] = "B"
      y2$ID2[y2$nLayer == "R2"] = "C"
      y2$ID2[y2$nLayer == "R1"] = "D"
      y2$ID2[y2$nLayer == "L4"] = "E"
      y2$ID2[y2$nLayer == "L3"] = "F"
      y2$ID2[y2$nLayer == "R4"] = "G"
      y2$ID2[y2$nLayer == "R3"] = "H"
      
    } else if (numPier == 9) {
      y2$ID2[y2$nLayer == "L3"] = "A"
      y2$ID2[y2$nLayer == "L2"] = "B"
      y2$ID2[y2$nLayer == "L1"] = "C"
      y2$ID2[y2$nLayer == "M3"] = "D"
      y2$ID2[y2$nLayer == "M2"] = "E"
      y2$ID2[y2$nLayer == "M1"] = "F"
      y2$ID2[y2$nLayer == "R3"] = "G"
      y2$ID2[y2$nLayer == "R2"] = "H"
      y2$ID2[y2$nLayer == "R1"] = "I"

    
  } else if (numPier == 12) {
    y2$ID2[y2$nLayer == "L4"] = "A"
    y2$ID2[y2$nLayer == "L3"] = "B"
    y2$ID2[y2$nLayer == "L2"] = "C"
    y2$ID2[y2$nLayer == "L1"] = "D"
    y2$ID2[y2$nLayer == "M4"] = "E"
    y2$ID2[y2$nLayer == "M3"] = "F"
    y2$ID2[y2$nLayer == "M2"] = "G"
    y2$ID2[y2$nLayer == "M1"] = "H"
    y2$ID2[y2$nLayer == "R4"] = "I"
    y2$ID2[y2$nLayer == "R3"] = "J"
    y2$ID2[y2$nLayer == "R2"] = "K"
    y2$ID2[y2$nLayer == "R1"] = "L"
  }
    
    temp = bind_rows(temp, y2)
  }

}

# Concatenate alphabet to pierNumber
temp$nPierNumber = paste(temp$PierNumber, temp$ID2, sep="")
#temp$nPierNumber[is.na(temp$nLayer)] = ""

# Remove hypen
temp$nPierNumber = gsub("-", "", temp$nPierNumber)

nrow(temp)

# Export
write.xlsx(temp, "Assign_alphabet_to_BoredPile_N2_xxxx.xlsx", row.names=FALSE, overwrite = TRUE)
