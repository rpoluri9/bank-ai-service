# Banking service image. Build the jar first: mvn -o package (or mvn package
# on a machine with network access), then: docker build -f banking-service/Dockerfile .
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY banking-service/target/banking-service-1.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
