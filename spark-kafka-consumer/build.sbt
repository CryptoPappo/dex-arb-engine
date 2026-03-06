name := "spark-kafka-consumer"

version := "0.1"

scalaVersion := "2.12.18"

libraryDependencies ++= Seq(
	"org.apache.spark" %% "spark-core" % "3.5.8",
	"org.apache.spark" %% "spark-sql" % "3.5.8",
	"org.apache.spark" %% "spark-sql-kafka-0-10" % "3.5.8",
	"org.apache.spark" %% "spark-protobuf" % "3.5.8"
)
