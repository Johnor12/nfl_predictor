# General rules

Write minimal, simple code and comments. Your goal is for the code to be human readable and understandable.

Group code into directories by abstraction/responsibility/API-to-the-rest-of-the-system. Include short README.mds in each directory which explain the directory's responsibility and API from an "external" (rest of the system) user's perspective. Each directory should have a small set of functions which are exposed to the rest of the system. Also include a short MAINTAINER.md in each directory, which lists the files in the directory and what their responsibilities are. At the top of each file, include a comment section with a START and END block. Inside the comment, include a short description of the functions in the file and their responsibilites, the goal being to allow an LLM agent to grep the starting comment and navigate the file without having to load it all into context. Whenever reading a file, start by reading the comment section.

Whenever working, read README.md and MAINTAINER.md at the root of the repo. You should never edit the root README.md by hand unless explicitly directed to. MAINTAINER.md has the same purpose as the MAINTAINER files in each directory; it should be a technical map of the project, and it's maintained by you. After any change, check if MAINTAINER.md needs to be updated.

Prefer systemic fixes when encountering parts of the system which weren't designed with the feature you're currently implementing in mind, rather than compromising clarity to fit the new feature into the existing system.

Design the system in a way which facilitates automated testing by agents.

Your goal when working should be to isolate the responsible service(s) and focus your work (and context) on them, treating other services as abstract APIs outside of the scope of your changes (only loading their README.mds into context, for example). The goal is to break the project into manageably sized services, allowing the project to scale with efficient context management (loading all project code into context on every change bloats quickly; loading a short <100 line README.md for each service scales much better).