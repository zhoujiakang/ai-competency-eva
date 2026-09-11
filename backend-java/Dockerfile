# 第一阶段：在容器里编译，服务器与本机都不需要预装 Java / Maven
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build
COPY . .
RUN chmod +x mvnw && ./mvnw -q -B -DskipTests package

# 第二阶段：只留运行时，镜像里没有 Maven 与源码
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /build/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
