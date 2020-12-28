library(rgdal)
library(sf)
library(dplyr)
library(stringr)
library(openxlsx)
library(tools)
library(stringr)

z = choose.dir()
wd = setwd(z)

a=file.choose()
y = read.xlsx(a)


######## find duplication
## Get owner trees which did not overlap original tree data.
y$n[is.na(y$n)]=0
min = min(y$n)
max = max(y$n)


mn = setdiff(min:max,y$n)
write.xlsx(mn,"lots_mustbe_bound_to_onlyIntersected_table.xlsx",row.names=FALSE)


yy=y[duplicated(y$n),]


write.xlsx(yyy,"duplicated_trees_owner_masterlist.xlsx",row.names=TRUE)

# Join the table (yy) to original (y)
## Note that the 'duplicated' function returns the 1st representative value of the duplicated. not all the duplicated value

yyy = left_join(y,yy,by="OBJECTID.*")
head(yyy)

##########

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
    temp[[k]] = gsub("[*]","",temp[[k]])
    temp[[k]] = gsub("\n","",temp[[k]])
    temp[[k]] = gsub("^\\s+|\\s+$", "",temp[[k]])
    
  }

  
}
colnames(temp)

############# Delete unwanted punctuation or numbers for only selected columns################
temp = y
ncol = colnames(temp)
dCol = select.list(ncol, multiple = TRUE, title = "Choose Target Columns") 


# Delete unwanted space;
for(i in dCol){
  temp[[i]] = gsub(" ","",temp[[i]])
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

# Convert to numeric column
for(i in dCol){
  temp[[i]] = as.numeric(temp[[i]])
}

# Delete Punctuation "*", "**", "\n", white space before 1st letter and after the last letter
for(i in dCol){
  temp[[i]] = gsub("[*]","",temp[[i]])
  temp[[i]] = gsub("\n","",temp[[i]])
  temp[[i]] = gsub("^\\s+|\\s+$", "",temp[[i]])
  
}

# Export
write.xlsx(temp,"y_new_priority_N2_20201223.xlsx",row.names = FALSE)

