#!/bin/bash
# Usage: source references/load-subtask-keys.sh <<story-key>>
# Loads all subtask keys from the given JIRA story into environment variables.

SUBTASKS=$(jira issue list --parent $1 --plain --columns key,summary)

SUB_CREATE_BRANCH=$(echo "$SUBTASKS"    | grep -i "Create branch"                          | awk '{print $1}')
SUB_UPDATE_ANGULAR=$(echo "$SUBTASKS"   | grep -i "Update Angular Version"                 | awk '{print $1}')
SUB_UPDATE_DEPS=$(echo "$SUBTASKS"      | grep -i "Update dependencies"                    | awk '{print $1}')
SUB_UPDATE_GUIDE=$(echo "$SUBTASKS"     | grep -i "Implement Angular Update Guide"         | awk '{print $1}')
SUB_NEW_FEATURES=$(echo "$SUBTASKS"     | grep -i "Implement New Angular Version features" | awk '{print $1}')
SUB_UNIT_TESTS=$(echo "$SUBTASKS"       | grep -i "Run unit tests"                         | awk '{print $1}')
SUB_COMPONENT_TESTS=$(echo "$SUBTASKS"  | grep -i "Run component tests"                    | awk '{print $1}')
SUB_SONARQUBE=$(echo "$SUBTASKS"        | grep -i "Check SonarQube"                        | awk '{print $1}')
SUB_CREATE_PR=$(echo "$SUBTASKS"        | grep -i "Create PR"                              | awk '{print $1}')
SUB_E2E_TESTS=$(echo "$SUBTASKS"        | grep -i "Run E2E"                                | awk '{print $1}')
SUB_MANUAL_TEST=$(echo "$SUBTASKS"      | grep -i "Manual test"                            | awk '{print $1}')
SUB_RELEASE=$(echo "$SUBTASKS"          | grep -i "^.*Release"                             | awk '{print $1}')
SUB_DEPLOY_STG=$(echo "$SUBTASKS"       | grep -i "Deploy to STG"                          | awk '{print $1}')

echo "Subtasks loaded:"
echo "  Create branch:              $SUB_CREATE_BRANCH"
echo "  Update Angular:             $SUB_UPDATE_ANGULAR"
echo "  Update dependencies:        $SUB_UPDATE_DEPS"
echo "  Update guide steps:         $SUB_UPDATE_GUIDE"
echo "  New features:               $SUB_NEW_FEATURES"
echo "  Unit tests:                 $SUB_UNIT_TESTS"
echo "  Component tests:            $SUB_COMPONENT_TESTS"
echo "  SonarQube:                  $SUB_SONARQUBE"
echo "  Create PR:                  $SUB_CREATE_PR"
echo "  E2E tests:                  $SUB_E2E_TESTS"
echo "  Manual test:                $SUB_MANUAL_TEST"
echo "  Release:                    $SUB_RELEASE"
echo "  Deploy to STG:              $SUB_DEPLOY_STG"
