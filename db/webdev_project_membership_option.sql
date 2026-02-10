-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: webdev_project
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `membership_option`
--

DROP TABLE IF EXISTS `membership_option`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `membership_option` (
  `id` int NOT NULL AUTO_INCREMENT,
  `gym_key` varchar(20) NOT NULL,
  `option_type` enum('gym_plan','addon') NOT NULL,
  `option_key` varchar(30) NOT NULL,
  `label` varchar(120) NOT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `price_with_full_gym_Access` decimal(10,2) DEFAULT NULL,
  `price_for_Add_ons_only` decimal(10,2) DEFAULT NULL,
  `discount_allowed` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_option` (`gym_key`,`option_type`,`option_key`),
  CONSTRAINT `fk_option_gym` FOREIGN KEY (`gym_key`) REFERENCES `gyms` (`gym_key`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `membership_option`
--

LOCK TABLES `membership_option` WRITE;
/*!40000 ALTER TABLE `membership_option` DISABLE KEYS */;
INSERT INTO `membership_option` VALUES (1,'ugym','gym_plan','super_off_peak','Super off-peak (10-12 & 2-4)',16.00,NULL,NULL,1),(2,'ugym','gym_plan','off_peak','Off-peak (12-2 & 8-11)',21.00,NULL,NULL,1),(3,'ugym','gym_plan','anytime','Anytime',30.00,NULL,NULL,1),(4,'ugym','addon','swim','Swimming pool',NULL,15.00,25.00,1),(5,'ugym','addon','classes','Classes',NULL,10.00,20.00,1),(6,'ugym','addon','massage','Massage therapy',NULL,25.00,30.00,0),(7,'ugym','addon','physio','Physiotherapy',NULL,20.00,25.00,0),(8,'power_zone','gym_plan','super_off_peak','Super off-peak',13.00,NULL,NULL,1),(9,'power_zone','gym_plan','off_peak','Off-peak',19.00,NULL,NULL,1),(10,'power_zone','gym_plan','anytime','Anytime',24.00,NULL,NULL,1),(11,'power_zone','addon','swim','Swimming pool',NULL,12.50,20.00,1),(12,'power_zone','addon','classes','Classes',NULL,0.00,20.00,1),(13,'power_zone','addon','massage','Massage therapy',NULL,25.00,30.00,0),(14,'power_zone','addon','physio','Physiotherapy',NULL,25.00,30.00,0);
/*!40000 ALTER TABLE `membership_option` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-09 11:57:02
