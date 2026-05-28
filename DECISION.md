1. Ambiguity raise at what kind of data can be input. 
2. To handle tenant wise, each source can have different columns names or keys, so i used json field to store raw data and render dynamic columns in UI with keys.
3. Here is a tenant specific raw data keys, each tenant need to follow once specific keys for each source
4. analytics I started working on analysis. computes the daily, yearly, monthly of unique set we use, here the data will be computed and stores in there period data.
5. Each source have 3 different periodic tables those are yearly, monthly,daily I felt this is analysis. so i just taken a standard keys(columns names).
6. At the time of storing raw data, i use rabbitMQ or redis, i will publish each record into queue and perform analysis in microservice which will handled asynchronously
7. In UI compute side menu will be added we will provide a api to provide analysis on data from that microservices
