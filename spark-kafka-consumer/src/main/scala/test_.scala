import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.protobuf.functions._
import org.apache.spark.sql.functions._

object KafkaConsumer {

  def main(args: Array[String]): Unit = {

    val spark = SparkSession.builder
      .appName("KafkaConsumer")
      .master("local[*]")
      .getOrCreate()

    import spark.implicits._

    val df = spark
      .readStream
      .format("kafka")
      .option("kafka.bootstrap.servers", "localhost:9092")
      .option("subscribe", "dex.swaps.raw")
      .option("startingOffsets", "latest")
      .load()

    val trades = df
      .select(
        from_protobuf(
          $"value",
          "dexarb.SwapEvent",
          "/home/jcpappo/dex-arb-engine/schemas/swap_event.desc"
        ).alias("events")
      )
      .select("events.chain_id", "events.liquidity", "events.tx_hash", "events.block_number", "events.timestamp")
     

    val query = trades.writeStream
      .format("console")
      .option("truncate", false)
      .start()

    query.awaitTermination()
  }
}
