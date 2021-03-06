tool_exec=function(in_params,out_params){
  library(rgdal)
  library(sf)
  library(dplyr)
  library(stringr)
  library(openxlsx)
  library(tools)
  library(stringr)
  
  ## RULES:
  # 1. Field names must match between old compiled master list table and new master tables (individual tables by Municipality)
  # 2. Field names must match between feature layer and compiled master list excel table.
  # 3. The sheet name of a new master list excel table must have municipality name.(e.g., MINALIN)
  # 4. Write a file name of new master list excel table using the same field names as in old master list table (e.g., Minalin_20200619.xlsx) 
  #
  ##
  
  ## Functions
  ## Capitalize the first letter
  CapStr <- function(y) {
    c <- strsplit(y, " ")[[1]]
    c = tolower(c)
    paste(toupper(substring(c, 1,1)), substring(c, 2),
          sep="", collapse=" ")
  }
  
  
  # A1:Parameters for ArcGIS Pro----
  workSpace=in_params[[1]] # parameter: workspace
  oldTable=in_params[[2]]
  newTable=in_params[[3]] # parameter: Table View, multiple values (ensure that csf files have station names: new master list)
  joinField=in_params[[4]] # Joine Field to be used between Old and New Master List tables
  result=out_params[[1]] # parameter: Feature Layer

# workSpace =   "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/NSCR-EX_envi/01-Environment/N2/Land_Acquisition/Master List/PAB-MASTERLIST/00-MasterList"
#  oldTable = "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/NSCR-EX_envi/01-Environment/N2/Land_Acquisition/Master List/PAB-MASTERLIST/00-MasterList/MasterList_Parcellary_Compiled.xlsx"
#  newTable = "C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\NSCR-EX_envi\\01-Environment\\N2\\Land_Acquisition\\Master List\\PAB-MASTERLIST\\Minalin\\Minalin_20200619.xlsx"
#  joinField = "LotID"

  # 1. Set Working Directory:
  dir=workSpace #"C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\NSCR-EX_envi\\99-Site_Preparation_Works\\Land_Acquisition\\Master List\\PAB-MASTERLIST"
  setwd(dir)

  # 3. Get names of municipality under the main directory
  ## 3.1 Extract Municipality name from Old Master List File Name:
  ##(Note we need to make sure municipality names match between old and new master list tables)
  print(oldTable)
  x=read.xlsx(gsub(paste("\\",basename(oldTable),sep=""),"",oldTable,fixed=TRUE)) # In the ArcGIS Pro, it reads the file at the level of a sheet name so need to remove it.
 # oldTable="C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\NSCR-EX_envi\\01-Environment\\N2\\Land_Acquisition\\Master List\\PAB-MASTERLIST\\00-MasterList\\Parcellary_MasterList_Compiled.xlsx\\T_Sheet_1$_"
  #x=read.xlsx(oldTable)
  
  listM=paste0(unique(x$Municipality),collapse="|")
  
  print(listM)

  ## Extract municipality names from new master list table
  ### Selected municipality

  print(newTable)
  municipality=str_extract(newTable,listM)
  print(municipality)
  
  # The number of extracted municipality from new master list in reference to old master list
  matchMu=unique(x$Municipality) %in% municipality
  length(which(matchMu==TRUE))
  
  # The number of municipality must be the same between selected and matched with original; othereise, STOP
  if(length(newTable)!=length(which(matchMu==TRUE))){ # if not equal stop
    stop("Municipality name(s) was not correctly selected from new master list(s): Check the file names of new master list")
    
  } else{
    # 4. Original Master List
    #a="C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\NSCR-EX_envi\\99-Site_Preparation_Works\\Land_Acquisition\\Master List\\PAB-MASTERLIST\\00-MasterList\\MasterList_Parcellary_Compiled.xlsx"
    #x=read.xlsx(a)
    
    #x=read.xlsx(oldTable)
    x=read.xlsx(gsub(paste("\\",basename(oldTable),sep=""),"",oldTable,fixed=TRUE))
    

    # 5. Delete Punctuation from New Master List Table and Compile:----
    # Create Empty table:
    TEMP=data.frame()
    
    for(i in municipality){
     # i="San Fernando"
      
 
      # Extract subject municipality name from the New master list excel table
      table=grep(i,newTable,ignore.case=TRUE,value=TRUE)
      #table="C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\NSCR-EX_envi\\01-Environment\\N2\\Land_Acquisition\\Master List\\PAB-MASTERLIST\\Malolos\\Malolos_20200714.xlsx\\Malolos$"
      #table="C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\NSCR-EX_envi\\01-Environment\\N2\\Land_Acquisition\\Master List\\PAB-MASTERLIST\\San_Fernando\\San Fernando_Parcellary_20200714.xlsx\\T_San_Fernando$_"
      
      # 5.4. Read New Master List Excel Table
      y=read.xlsx(gsub(paste("\\",basename(table),sep=""),"",table,fixed=TRUE)) # Remove [1] later
      #y=read.xlsx(table) # Remove [1] later

      # 5.6. Delete Redundant Punctuations from Observations:
      ## 5.6.1. Create empty table:
      temp=as.data.frame(matrix(data=NA,nrow=nrow(y),ncol=length(colnames(y))))
      colnames(temp)=colnames(y)
      
      for(j in colnames(y)){
        #j=colnames(y)[1]
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
        # Delete Punctuation "*" or "**" & "\n", " "#
        #############################################

        # Ensure that Total Area is numeric:
        if(j==grep("TotalArea",colnames(y),value=TRUE)){
          temp[[j]]=as.numeric(temp[[j]])
        } else {
          temp[[j]]=gsub("[*]","",temp[[j]])
          temp[[j]]=gsub("\n","",temp[[j]])
          #temp[[j]]=gsub(" ","",temp[[j]])
          temp[[j]]=gsub("[*]","",temp[[j]])
        }
      }
      
      # Add Municipality
      temp$Municipality=i
      tail(temp)

      # End of Delete Punctuation
      
      # 5.7 Compile All Municipalities
      TEMP=bind_rows(TEMP,temp)
      
    }
# OK until here
    # 6. Replace Original Master List with New Master List compiled
    
    TABLE=data.frame()
    #for(k in toupper(municipality)){
v=1
    for(k in municipality){
      #k="Malolos"
      # Join TEMP (new master list) to original
      ## Extract missing field names from New Master List that exist in the original master list
      if(v==1){
        unFieldN=colnames(x)[!colnames(x) %in% colnames(TEMP)]
        ## Extract sub datasets of missing field names from original Master List
        # x10=x[,c(fieldNames[1],fieldNames[2],unFieldN)]
        x10=x[,c(joinField,"Municipality",unFieldN)]
        x11=filter(x10,Municipality==k)
        x11=x11[,-which(colnames(x11)=="Municipality")]
        
        ## Join TEMP (new master list) to original for missing
        TEMP_Filter=filter(TEMP,Municipality==k)
        #ok
        xxx=left_join(TEMP_Filter,x11,by=joinField)
        
        # Filter out municipality selected from original master list:
        TABLE=filter(x,Municipality!=k)
      } else {
        unFieldN=colnames(TABLE)[!colnames(x) %in% colnames(TEMP)]
        ## Extract sub datasets of missing field names from original Master List
        # x10=x[,c(fieldNames[1],fieldNames[2],unFieldN)]
        x10=x[,c(joinField,"Municipality",unFieldN)]
        x11=filter(x10,Municipality==k)
        x11=x11[,-which(colnames(x11)=="Municipality")]
        
        ## Join TEMP (new master list) to original for missing
        TEMP_Filter=filter(TEMP,Municipality==k)
        #ok
        xxx=left_join(TEMP_Filter,x11,by=joinField)
        
        # Filter out municipality selected from original master list:
        TABLE=filter(TABLE,Municipality!=k)
      }


        # Row bind new master list to original master list 
        TABLE$TotalArea=as.numeric(TABLE$TotalArea)
        TABLE=bind_rows(TABLE,xxx)
        
        v=v+1


    }
    
  # 7. Delete Redundant Space for LotNo and SurveyNo
    # Delete a space for Survey No
    TABLE[,which(colnames(TABLE)=="SurveyNo")]=gsub(" ","",TABLE$SurveyNo)

    ## Add space before and after bracket "()"
    ngrep=grep(")P", TABLE$SurveyNo)
    id=which(colnames(TABLE)=="SurveyNo")
    TABLE[ngrep,id]=gsub(")P",") P",TABLE[ngrep,id])
    
    
    # Lot No
    ## Delete space before Lot
    TABLE[,which(colnames(TABLE)=="LotNo")]=gsub(" Lot", "Lot",TABLE$LotNo)
    
    ## Replace observations of " " with NA
    TABLE[which(nchar(TABLE$LotNo)==1),which(colnames(TABLE)=="LotNo")]=NA
    
    ngrep=grep("LOT|LOTS",TABLE$LotNo)
    id=which(colnames(TABLE)=="LotNo")
    TABLE[ngrep,id]=gsub("LOT","Lot",TABLE[ngrep,id])
    
  # 8. Capitalize the first letter of Municipality
    #TABLE[,which(colnames(TABLE)=="Municipality")]=CapStr(TABLE$Municipality)
 #
################ ################# #################
    
    # Assign correct process to Field Name: Status
    # Fill in Names:
    ## Extract colnames

    nColOtBC=which(colnames(TABLE)=="OtB_Name"|colnames(TABLE)=="OtC_Name")
    nColPrep=which(colnames(TABLE)=="OtB_Preparation"|colnames(TABLE)=="OtC_Preparation")
    nColDeliv=which(colnames(TABLE)=="OtB_Delivered"|colnames(TABLE)=="OtC_Delivered")
    nColStatus_OtBC=which(colnames(TABLE)=="OtB_Status"|colnames(TABLE)=="OtC_Status")
    
    nColPayPExpro=which(colnames(TABLE)=="PP_EC_Name")
    nColPayP=which(colnames(TABLE)=="Payment_Processing")
    nColExproC=which(colnames(TABLE)=="Expropriation_Case")
    nColStatusPayExpro=which(colnames(TABLE)=="PP_EC_Status")

    ## OtB/OtC_Name:
    TABLE[nColOtBC][TABLE[nColPrep]>=1]=colnames(TABLE)[nColPrep]
    TABLE[nColOtBC][TABLE[nColDeliv]>=1]=colnames(TABLE)[nColDeliv]
   
    ## Paypment Processing & Expropriation Case Name
    TABLE[nColPayPExpro][TABLE[nColPayP]>=1]=colnames(TABLE)[nColPayP]
    TABLE[nColPayPExpro][TABLE[nColExproC]>=1]=colnames(TABLE)[nColExproC]
    
    # Fill in Status:
    ## OtB/OtC_Preparation and Delivered
    if(grepl("OtB",colnames(TABLE)[nColOtBC],ignore.case = TRUE)){
      TABLE=mutate(TABLE,OtB_Status=ifelse(OtB_Name==colnames(TABLE)[nColPrep],OtB_Preparation,OtB_Delivered+5))
      TABLE=mutate(TABLE,OtB_Status=ifelse(is.na(OtB_Status),0,OtB_Status))
    } else {
      TABLE=mutate(TABLE,OtC_Status=ifelse(OtC_Name==colnames(TABLE)[nColPrep],OtC_Preparation,OtC_Delivered+5))
      TABLE=mutate(TABLE,OtC_Status=ifelse(is.na(OtC_Status),0,OtC_Status))
    }

    ## Payment Processing and Expropriation Case
    TABLE=mutate(TABLE,PP_EC_Status=ifelse(PP_EC_Name==colnames(TABLE)[nColPayP],Payment_Processing,Expropriation_Case+4)) 
    TABLE=mutate(TABLE,PP_EC_Status=ifelse(is.na(PP_EC_Status),0,PP_EC_Status))
    
    # Re-define "Scale" as numeric and 0 for NA
    TABLE$Scale[is.na(TABLE$Scale)]=0
    
    # Re-order by unid
    TABLE=TABLE[order(TABLE$unid), ]
    
    # Remove all spaces for numeric field
    TABLE$AffectedArea=as.numeric(TABLE$AffectedArea)
    TABLE$Scale=as.numeric(TABLE$Scale)
    
    #Export as xlsx
    write.xlsx(TABLE,file.path(dir,paste("MasterList_Parcellary_Compiled","_",Sys.Date(),".xlsx",sep="")))
    
    # Export result table:
    arc.write(result,TABLE,overwrite=TRUE)
    
    # return result
    return(out_params)
    
  }
  }