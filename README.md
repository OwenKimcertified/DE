# python TIL

backend

DB

airflow

k8s
- Deployment, Values

aws (boto3)

CDC 

          Master (CUD)
        +-----------------+
        |   MySQL Master  |  Binlog
        +-----------------+   |  
                |            |  (CDC)
                ▼            |
        [ Python CDC pipe ]
                | Apply Changes
                ▼ 
        +-----------------+
        |   MySQL Slave   |  R
        +-----------------+

