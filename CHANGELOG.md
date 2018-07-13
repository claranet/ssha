# 1.5.1

* Improve error messages for SSH config issues

# 1.5.0

* Allow the bastion to be disabled #66

# 1.4.0

* Fix for instances with missing tags #64
* Multi-region support #65

# 1.3.0

* Fix possible unicode errors #60
* Allow wildcards on config names #61
* Allow setting the bastion hostname directly #62
* Add support for TagsNotEqual #63

# 1.2.2

* Fix single character username #58

# 1.2.1

* Use Paramiko to parse SSH config #56

# 1.2.0

* Add argument for custom .ssha file location #48
* Allow user to enter MFA code again after receiving an error #49
* Add version check to .ssha file #50

# 1.1.0

* Python 3 support #44
* Always use private IP when connecting through a bastion #45

# 1.0.1

* Fix crash if no instances returned #42

# 1.0.0

* Add scrolling when there are too many instances to fit on screen #37
* Improve how instances are displayed by aligning fields #40

# 0.9.0

* Fix pagination of SSM instances #31 #32
* Use default SSH name and identity file #33
