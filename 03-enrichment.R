#install.packages("dplyr")
#install.packages("ggplot2")
#install.packages("tidyverse")
#install.packages("openxlsx")

library (dplyr)
library (ggplot2)  
library(tidyverse)
library(openxlsx)
 
BP = read.csv('GO_BP.txt',sep='\t')
CC = read.csv('GO_CC.txt',sep='\t')
MF = read.csv('GO_MF.txt',sep='\t')
 
head(BP)
 
BP = separate(BP,Term, sep="~",into=c("ID","Description"))
CC = separate(CC,Term, sep="~",into=c("ID","Description"))
MF = separate(MF,Term, sep="~",into=c("ID","Description"))

 
display_number = c(5, 8, 8)  
 
go_result_BP = as.data.frame(BP)[1:display_number[1], ]
go_result_CC = as.data.frame(CC)[1:display_number[2], ]
go_result_MF = as.data.frame(MF)[1:display_number[3], ]
 

 
go_enrich = data.frame(
  ID=c(go_result_BP$ID, go_result_CC$ID, go_result_MF$ID),                       
  Description=c(go_result_BP$Description,go_result_CC$Description,go_result_MF$Description),
  GeneNumber=c(go_result_BP$Count, go_result_CC$Count, go_result_MF$Count),
 
  type=factor(c(rep("Biological Process", display_number[1]),
                rep("Cellular Component", display_number[2]),
                rep("Molecular Function", display_number[3])),
              levels=c("Biological Process", "Cellular Component","Molecular Function" )))
 
 
 
for(i in 1:nrow(go_enrich)){
  description_splite=strsplit(go_enrich$Description[i],split = " ")
  description_collapse=paste(description_splite[[1]][1:5],collapse = " ") 
  go_enrich$Description[i]=description_collapse
  go_enrich$Description=gsub(pattern = "NA","",go_enrich$Description)  
}
 
#go_enrich$type_order = factor(go_enrich$Description,levels=go_enrich$Description,ordered = T)
unique_descriptions <- unique(go_enrich$Description)

go_enrich$type_order <- factor(go_enrich$Description, levels = unique_descriptions, ordered = TRUE)

head(go_enrich)

p <- ggplot(go_enrich,
       aes(x=type_order,y=GeneNumber, fill=type)) + 
       geom_bar(stat="identity", width=0.8) +  
       scale_fill_manual(values = c("#6666FF", "#33CC33", "#FF6666")) +  
       coord_flip() +  
       theme_bw() +
        theme(
          axis.title.x = element_blank(),
          axis.title.y = element_blank(),
          plot.title = element_blank(),
          axis.text.y = element_text(size = 15),  
          axis.text.x = element_text(size = 15)
        #  axis.title.y = element_text(size = 14) 
        )
ggsave("go_enrichment.png", plot = p, dpi = 300, width = 13, height = 8)


kk_result= read.csv('KEGG.txt', sep = '\t')


display_number = 10

kk_result = as.data.frame(kk_result)[1:display_number[1], ]

kk = as.data.frame(kk_result)

rownames(kk) = 1:nrow(kk)

kk$order=factor(rev(as.integer(rownames(kk))),labels = rev(kk$Term))


p <- ggplot(kk,aes(y=order,x=Benjamini))+
  
  geom_point(aes(size=Count,color=PValue))+
  
  scale_color_gradient(low = "red",high ="blue")+
  
  labs(color=expression(PValue,size="Count"))+
  
  theme_bw()+
  theme(
    axis.title.x = element_blank(),
    axis.title.y = element_blank(),
    plot.title = element_blank(),
    axis.text.y = element_text(size = 15),  
    axis.text.x = element_text(size = 15)
  )

ggsave("kegg_pathway_enrichment.png", plot = p, dpi = 300, width = 13, height = 8)
