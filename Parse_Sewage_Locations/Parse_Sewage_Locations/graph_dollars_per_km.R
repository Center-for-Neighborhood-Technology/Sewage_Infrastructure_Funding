library(readr)
library(ggplot2)
library(dplyr)

dollars_per_km <- read_csv('dollars_per_km.csv')
dpkm_ssrc <- dollars_per_km %>% filter(project_group == "sewer system replacement and construction", dollars_per_km < 10000000)
dpkm_sl <- dollars_per_km %>% filter(project_group == "sewer lining")

hist(dpkm_ssrc$dollars_per_km_four_year, xlim = c(0,10000000), breaks=50)
boxplot(dpkm_ssrc$dollars_per_km_four_year)
hist(dpkm_ssrc$dollars_per_km_total)
boxplot(dpkm_ssrc$dollars_per_km_total)

hist(dpkm_sl$dollars_per_km_four_year)
boxplot(dpkm_sl$dollars_per_km_four_year)
hist(dpkm_sl$dollars_per_km_total)
boxplot(dpkm_sl$dollars_per_km_total)
