#!/bin/bash
mysql -u root -h localhost --password=root 'tymenu' < $1
