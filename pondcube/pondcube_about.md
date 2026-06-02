# PondCube

## Aim

PondCube is a real-time water-quality monitoring system for aquaculture. Digital probes in the tanks continuously record key parameters and stream them to the cloud, where a mobile app lets farm staff watch live conditions and get alerted the moment something drifts out of a safe range.

## How it works

- **Sense.** Digital probes in each tank record temperature and dissolved oxygen continuously (sampling interval to be defined — likely around every 30 minutes).
- **Send.** Probes push their readings to the cloud (Google) through an ingestion API.
- **Serve.** A second API delivers the data from the cloud to a mobile application.
- **Monitor.** The app shows current levels and trends per tank.
- **Alert.** When a parameter crosses its threshold, the system triggers a notification to the app so staff can act fast.

## Why it matters

Water conditions can turn dangerous quickly, and dissolved oxygen in particular can crash within hours. Continuous sensing plus instant alerts means problems are caught early instead of at the next manual check — protecting stock, reducing losses, and freeing staff from constant manual readings.

## In short

PondCube connects probe, cloud, and phone into one loop: measure continuously, monitor live, and alert automatically.