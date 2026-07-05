FROM node:18-slim
WORKDIR /app
RUN npm install @whiskeysockets/baileys @hapi/boom
COPY wa_node.js .
COPY bot.py .
COPY requirements.txt .
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install --no-cache-dir -r requirements.txt
CMD ["python3", "bot.py"]
