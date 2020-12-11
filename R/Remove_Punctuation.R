library(rgdal)
library(sf)
library(dplyr)
library(stringr)
library(openxlsx)
library(tools)

z = choose.dir()
wd = setwd(z)

a=file.choose()
y = read.xlsx(a)


temp=as.data.frame(matrix(data=NA,nrow=nrow(y),ncol=length(colnames(y))))
colnames(temp)=colnames(y)

for(j in colnames(y)){
  #j=1
  nrow=1:length(y[[j]])
  
  ###################################
  # Delete Punctuation indepent "-" #
  ###################################
  
  # Exract Row number in Pattern "xx_xx": S1
  nrow_s1=grep("\\w-\\w",y[[j]]) # xx-xx
  s1=grep("\\w-\\w",y[[j]],value=TRUE)
  s1_logical=unique(grepl("\\w-\\w",y[[j]]))
  
  # Extract only "-": S2
  ## If number of s1 row is zero, it is equal to total observation number (nrow)
  if(length(nrow_s1)==0){
    nrow_s2=nrow
    s2=y[[j]]
    
    ## Otherwise, 
  } else {
    nrow_s2=nrow[-nrow_s1]
    s2=y[[j]][-nrow_s1] # only "_" or others
  }
  
  ## Replace "-" with ""
  s2=gsub("-","",s2,fixed=TRUE)
  s2_len=length(gsub("-","",s2,fixed=TRUE))
  
  # Combine S1 and S2
  NN=vector(mode="character", length=length(nrow))
  
  ## if no "-" was found, just use original observations:
  if(s1_logical==FALSE && s2_len==0){
    temp[j]=y[[j]]
    
    ## Otherwise, combine
  } else {
    NN[nrow_s2]=s2
    NN[nrow_s1]=s1
    temp[j]=NN
    
  }
  
  #############################################
  # Delete Punctuation "*", "**", "\n", white space before 1st letter and after the last letter
  #############################################
  for(k in colnames(temp)){
    k = colnames(temp1)[1]
    temp[[k]] = gsub("[*]","",temp[[k]])
    temp[[k]] = gsub("\n","",temp[[k]])
    temp[[k]] = gsub("^\\s+|\\s+$", "",temp[[k]])
    
  }

  
}


# Delete unwanted space
temp1$C = gsub(" ","",temp1$C)

#
write.xlsx(temp1,"sample.xlsx",row.names = FALSE)
