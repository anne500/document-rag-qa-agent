# Project Cedar: Build and Release Notes

This is a fictional project used for testing a document Q&A assistant.

## Automated tests
Project Cedar runs automated tests whenever a pull request is opened.
Regression tests check that existing behavior still works after a change.
Passing tests does not prove that the software has no defects.

## Release policy
A failed required test blocks the release workflow until the problem is reviewed.
A release requires all required tests to pass and approval from a maintainer.

## Build failure example
Build CEDAR-104 failed because the dependency cedar-utils==9.9.9 could not
be found in the configured package index.
The proposed next action is to verify the dependency version and package
index configuration before running the build again.

## Missing information
This document does not specify a production deployment date or a cloud provider.
