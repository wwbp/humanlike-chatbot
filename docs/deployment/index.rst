Deployment
==========

The ChatLab deployment system automates the process of launching your chatbot
infrastructure on AWS — including databases, caching, web servers, SSL, and
content delivery networks — using Terraform and GitHub Actions.

This section explains how to **deploy**, **manage**, and **reset** your ChatLab
infrastructure in a safe and repeatable way. Whether you are setting up ChatLab
for the first time or refreshing your existing environment, the workflows
outlined here will handle all configuration and provisioning automatically.

Overview
--------

ChatLab's deployment process uses **infrastructure-as-code** to guarantee that
every researcher can reproduce a working setup without needing deep cloud
expertise. Once configured, deployment takes only a few clicks via GitHub.

Typical setup flow:

1. Use the :doc:`deploy` workflow to launch ChatLab on AWS.
2. Manage or temporarily remove your infrastructure with :doc:`destroy`.
3. Run :doc:`reset` only when you need a completely clean environment.

Workflows
---------

.. toctree::
   :maxdepth: 1

   for-researchers
   workflow-guide
   deploy
   destroy
   reset
   aws-deployment
   technical-reference
