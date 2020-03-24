tool_exec=function(in_params,out_params){
  library(rgdal)
  library(sf)
  library(dplyr)
  library(stringr)
  library(openxlsx)
  
  # A1:Parameters for ArcGIS Pro----
  workSpace=in_params[[1]] # parameter: workspace
  oldTable=in_params[[2]]
  newTable=in_params[[3]] # parameter: Table View, multiple values (ensure that csf files have station names: new master list)
  joinField=in_params[[4]] # Joine Field to be used between Old and New Master List tables
  result=out_params[[1]] # parameter: Feature Layer

  # 1. Set Working Directory:
  dir=workSpace #"C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\NSCR-EX_envi\\99-Site_Preparation_Works\\Land_Acquisition\\Master List\\PAB-MASTERLIST"
  setwd(dir)
  
  # 3. Get names of municipality under the main directory
  municipality=str_extract(newTable, "Apalit|Angeles|Apalit|Calumpit|Mabalacat|Malolos|Minalin|Fernando|Tomas")

  # 4. Original Master List
  #a="C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\NSCR-EX_envi\\99-Site_Preparation_Works\\Land_Acquisition\\Master List\\PAB-MASTERLIST\\00-MasterList\\MasterList_Parcellary_Compiled.xlsx"
  #x=read.xlsx(a)
  
  x=read.xlsx(gsub(paste("\\",basename(oldTable),sep=""),"",oldTable,fixed=TRUE))

  
# 5. Delete Punctuation from New Master List Table and Compile:----
  # Create Empty table:
  TEMP=data.frame()

  for(i in municipality){

    table=grep(i,newTable,ignore.case=TRUE,value=TRUE)

    # 5.4. Read New Master List Excel Table
    y=read.xlsx(gsub(paste("\\",basename(table),sep=""),"",table,fixed=TRUE)) # Remove [1] later

    # 5.6. Delete Redundant Punctuations from Observations:
    ## 5.6.1. Create empty table:
    temp=as.data.frame(matrix(data=NA,nrow=nrow(y),ncol=length(colnames(y))))
    colnames(temp)=colnames(y)

    for(j in colnames(y)){
      #j=colnames(y)[1]
      nrow=1:length(y[[j]])
      
      ##########################
      # Delete Punctuation "-" #
      ##########################
      
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
      
      ##################################
      # Delete Punctuation "*" or "**" #
      ##################################
      
      # If CN, delete ** or *:
      if(j==grep("CN",colnames(y),value=TRUE)){
        temp[[j]]=gsub("[*]","",temp[[j]])
      }
      
      # Ensure that Total Area is numeric:
      if(j==grep("TotalArea",colnames(y),value=TRUE)){
        temp[[j]]=as.numeric(temp[[j]])
      }
    }

    # Add Municipality
    temp$Municipality=toupper(i)
    
    # End of Delete Punctuation
    
    # 5.7 Compile All Municipalities
    TEMP=bind_rows(TEMP,temp)
    
  }
  
# 6. Replace Original Master List with New Master List compiled
  
  TABLE=data.frame()
  for(k in toupper(municipality)){

    # Join TEMP (new master list) to original
    ## Extract missing field names from New Master List that exist in the original master list
    unFieldN=colnames(x)[!colnames(x) %in% colnames(TEMP)]
    
    ## Extract sub datasets of missing field names from original Master List
   # x10=x[,c(fieldNames[1],fieldNames[2],unFieldN)]
    x10=x[,c("LotID","Municipality",unFieldN)]
    x11=filter(x10,Municipality==k)
    x11=x11[,-which(colnames(x11)=="Municipality")]

    ## Join TEMP (new master list) to original for missing
    TEMP_Filter=filter(TEMP,Municipality==k)
    xxx=left_join(TEMP_Filter,x11,by=joinField)

    # Filter out municipality selected from original master list:
    TABLE=filter(x,Municipality!=k)
    
    # Row bind new master list to original master list 
    TABLE$TotalArea=as.numeric(TABLE$TotalArea)

    TABLE=bind_rows(TABLE,xxx)
    
  }

  # Re-define "Scale" as numeric and 0 for NA
  TABLE$Scale[is.na(TABLE$Scale)]=0
  
  # Re-order by unid
  TABLE=TABLE[order(TABLE$unid), ]

  # Remove all spaces for numeric field
  TABLE$AffectedArea=as.numeric(TABLE$AffectedArea)
  TABLE$Scale=as.numeric(TABLE$Scale)
  
  #Export as xlsx
  write.xlsx(TABLE,file.path(dir,"MasterList_Parcellary_Compiled.xlsx"))

  # Export result table:
  arc.write(result,TABLE,overwrite=TRUE)
  
  # return result
  return(out_params)

}