# Stage 1: Build Java application
FROM maven:3.9.6-eclipse-temurin-21 AS builder
WORKDIR /build
COPY java-sim/pom.xml .
# Download dependencies first (cached layer)
RUN mvn dependency:go-offline
COPY java-sim/src ./src
RUN mvn clean package

# Stage 2: Runtime image
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=builder /build/target/java-sim-1.0.0.jar ./gateway.jar
EXPOSE 25333
ENTRYPOINT ["java", "--enable-native-access=ALL-UNNAMED", "-jar", "gateway.jar"]