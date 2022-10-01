FROM python:3.10.7-bullseye

RUN apt update && apt install build-essential cmake -y

WORKDIR /app
COPY ./ ./

RUN pip3 install -e .


# Write in .bashrc file python -m fishery 
RUN echo "python -m fishery" >> ~/.bashrc

# Expose port for osc server
EXPOSE 23000

CMD ["/bin/bash"]

