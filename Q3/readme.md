# Youtube server using RabbitMQ

An implementation of a youtube server using RabbitMQ

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)

## Installation

### Prerequisites
- Python 3.6 or higher

### Installation
Clone the repository
```bash
git clone https://github.com/utkar22/DSCD-A1-G1.git
```

```bash
cd DSCD-A1-G1
```

```bash
cd Q3
```

```bash
chmod +x setup_rabbitmq.sh
```

```bash
./setup.sh
```


## Usage

Run the youtube server by using the following command:

```bash
python3 youtube_server.py 
```

Publish a youtube video by using the following command:

```bash
python3 youtuber.py <YoutuberName> <VideoName>
```


Login as user by using the following command:

```bash
python3 user.py <username>
```

Subscribe to a youtuber by using the following command:

```bash
python3 user.py <username> s <YoutuberName>
```

Unsubscribe to a youtuber by using the following command:

```bash
python3 user.py <username> u <YoutuberName>
```