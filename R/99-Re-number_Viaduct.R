# This code is used to re-number Viaduct bored piles


# Make sure to sort by shape in ascending order in ArcGIS Pro first#
# N2: Sort lower right (chainage direction from S to N)
# SC: Sot upper left (chainage direction from N to S)

library(openxlsx)
library(dplyr)
library(stringr)

z = choose.dir()
wd = setwd(z)


# Read "L"
a=file.choose()
y = read.xlsx(a)

y$pp = 0

#
pier = unique(y$PierNumber)
temp = data.frame()

head(y)
for(i in pier){
  x = y[y$PierNumber==i,]
  x$pp = 1:nrow(x)
  
  temp = bind_rows(temp,x)
}
unique(temp$pp)
head(temp,20)

write.xlsx(temp,file.path(wd,"SC_Viaduct_L_sorted_N_to_S_numbered.xlsx"))

## Join "L" to M
#aL=file.choose()
L = read.xlsx(file.path(wd,"SC_Viaduct_L_sorted_N_to_S_numbered.xlsx"))
head(L)

tempL = data.frame()
pier = unique(L$PierNumber)
for(i in pier){
  x = L[L$PierNumber==i,]
  max = max(x$pp)
  x = x[x$pp==max,]
  tempL = bind_rows(tempL,x)
  
}

# Read M
aM=file.choose()
M=read.xlsx(aM)
head(M)



# join
head(tempL)
#id = which(colnames(tempLM)=="PierNumber" | colnames(tempLM)=="pp")
id = which(colnames(tempL)=="PierNumber" | colnames(tempL)=="pp")
Lx = tempL[,id]

MLx = left_join(M,Lx,by="PierNumber")
head(MLx)
MLx$ppM = 0

pier = unique(MLx$PierNumber)
tempM = data.frame()

for(i in pier) {
  x = MLx[MLx$PierNumber==i,]
  max=max(x$pp)
  nrow = 1:nrow(x) + max
  x$ppM = nrow
  
  tempM = bind_rows(tempM,x)
}
head(tempM)

tempM = tempM[,-(ncol(tempM)-1)]
colnames(tempM)[ncol(tempM)] = "pp"
head(tempM)

write.xlsx(tempM,file.path(wd,"SC_Viaduct_M_sorted_N_to_S_numbered.xlsx"))

# Append L and M
L = read.xlsx(file.path(wd,"SC_Viaduct_L_sorted_N_to_S_numbered.xlsx"))
M = read.xlsx(file.path(wd, "SC_Viaduct_M_sorted_N_to_S_numbered.xlsx"))

head(L)
head(M)
LM = bind_rows(L,M)

LM = LM[order(LM$PierNumber),]

## join "LM" to R
### only choose nPienrnUmber with max pp
tempLM = data.frame()
pier = unique(LM$PierNumber)
for(i in pier){
  x = LM[LM$PierNumber==i,]
  max = max(x$pp)
  x = x[x$pp==max,]
  tempLM = bind_rows(tempLM,x)
  
}
head(tempLM)

# Read R
aR=file.choose()
R=read.xlsx(aR)
head(R)


# join
head(tempLM)
id = which(colnames(tempLM)=="PierNumber" | colnames(tempLM)=="pp")
LMx = tempLM[,id]

unique(R$PierNumber)
unique(LMx$PierNumber)

LMR = left_join(R,LMx,by="PierNumber")
head(LMR,100)

LMR$ppR = 0

head(LMR)

pier = unique(LMR$PierNumber)
tempLMR = data.frame()

for(i in pier) {
  x = LMR[LMR$PierNumber==i,]
  max=max(x$pp)
  nrow = 1:nrow(x) + max
  x$ppR = nrow
  
  tempLMR = bind_rows(tempLMR,x)
}
head(tempLMR)

tempLMR = tempLMR[,-(ncol(tempLMR)-1)]
colnames(tempLMR)[ncol(tempLMR)] = "pp"

write.xlsx(tempLMR,file.path(wd,"SC_Viaduct_R_sorted_N_to_S_numbered.xlsx"))

# Append L, M, R 
L=read.xlsx(file.path(wd,"SC_Viaduct_L_sorted_N_to_S_numbered.xlsx"))
M=read.xlsx(file.path(wd,"SC_Viaduct_M_sorted_N_to_S_numbered.xlsx"))
R=read.xlsx(file.path(wd,"SC_Viaduct_R_sorted_N_to_S_numbered.xlsx"))

head(L);head(M);head(R)
LMR=rbind(L,M,R)


LMR = LMR[order(LMR$PierNumber),]
write.xlsx(tempLMR,file.path(wd,"SC_Viaduct_LMR_sorted_N_to_S_numbered_temp.xlsx"))

# Re-format 
str(LMR)
LMR$pp[is.na(LMR$pp)]=0
LMR$pp2 = "0"

LMR$pp2=paste("0",LMR$pp,sep = "")

write.xlsx(LMR,file.path(wd,"SC_Viaduct_LMR_sorted_N_to_S_numbered_final.xlsx"))
