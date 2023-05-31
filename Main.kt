package com
import kotlin.system.measureTimeMillis
import java.net.HttpURLConnection
import java.net.URL


fun  main(){
    val executionTime = measureTimeMillis{ getRequest() }
    println("Execution time: $executionTime ms")
}

fun getRequest() {
    print("Enter the url : ")
    val url = URL(readln())
    val connection = url.openConnection() as HttpURLConnection
    connection.requestMethod = "GET"

    if (connection.responseCode == HttpURLConnection.HTTP_OK) {
        val response = connection.inputStream.bufferedReader().readText()
        println(response)
    } else {
        println("HTTP Error: ${connection.responseCode}")
    }

    connection.disconnect()
    println("Used Memory: ${getJvmMemoryUsage()} Mbytes")
}

fun getJvmMemoryUsage() : Float {
    Runtime.getRuntime().gc()
    val usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()
    val convertedMbytes : Double = (usedMemory.toFloat()/1024)*0.001
    return convertedMbytes.toFloat()
}