// Package deploymentmanager provides utilities for deployment manager.
package deploymentmanager

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"

	"github.com/ghodss/yaml"
)

// The following vars are stubbed in tests.
var (
	cmdRun            = (*exec.Cmd).Run
	cmdCombinedOutput = (*exec.Cmd).CombinedOutput
)

// Deployment represents a single deployment which can be used by the GCP Deployment Manager.
// TODO: move into separate package.
type Deployment struct {
	Imports   []*Import   `json:"imports,omitempty"`
	Resources []*Resource `json:"resources"`
}

// Import respresents a deployment manager template import.
type Import struct {
	Path string `json:"path"`
}

// Resource defines the deployment manager resources to deploy.
type Resource struct {
	Name       string                 `json:"name"`
	Type       string                 `json:"type"`
	Properties map[string]interface{} `json:"properties,omitempty"`
	Metadata   *Metadata              `json:"metadata,omitempty"`
}

// Metadata contains extra metadata of the deployment.
type Metadata struct {
	DependsOn []string `json:"dependsOn,omitempty"`
}

// Upsert creates the deployment if it does not exist, else updates it.
func Upsert(name string, deployment *Deployment, projectID string) error {
	b, err := yaml.Marshal(deployment)
	if err != nil {
		return fmt.Errorf("failed to marshal deployment : %v", err)
	}
	log.Printf("Creating deployment %q:\n%v", name, string(b))

	tmp, err := ioutil.TempFile("", "")
	if err != nil {
		return fmt.Errorf("failed to create temp file: %v", err)
	}
	defer os.Remove(tmp.Name())

	if _, err := tmp.Write(b); err != nil {
		return fmt.Errorf("failed to write deployment to file: %v", err)
	}
	if err := tmp.Close(); err != nil {
		return fmt.Errorf("failed to close temp file: %v", err)
	}
	return UpsertFromFile(name, tmp.Name(), projectID)
}

// UpsertFromFile creates the deployment from a YAML file if the deployment does not exist, else
// updates it.
func UpsertFromFile(name, fileName string, projectID string) error {
	exists, err := checkDeploymentExists(name, projectID)
	if err != nil {
		return fmt.Errorf("failed to check if deployment exists: %v", err)
	}

	args := []string{"deployment-manager", "deployments"}
	if exists {
		// Due to the sensitive nature of the resources we manage, we don't want to
		// delete any resources after they have been deployed. Instead, abandon the resource
		// so the user can manually delete them later on.
		args = append(args, "update", name, "--delete-policy", "ABANDON")
	} else {
		args = append(args, "create", name)
	}
	args = append(args, "--project", projectID, "--config", fileName)

	log.Printf("Running gcloud command with args: %v", args)

	cmd := exec.Command("gcloud", args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stdout
	if err := cmdRun(cmd); err != nil {
		return fmt.Errorf("failed to run command: %v", err)
	}
	return nil
}

// checkDeploymentExists determines whether the deployment with the given name exists in the given project.
func checkDeploymentExists(name, projectID string) (bool, error) {
	type deploymentInfo struct {
		Name string `json:"name"`
	}

	cmd := exec.Command("gcloud", "deployment-manager", "deployments", "list", "--format", "json", "--project", projectID)

	out, err := cmdCombinedOutput(cmd)
	if err != nil {
		return false, fmt.Errorf("failed to run command: %v\n%v", err, string(out))
	}

	deploymentInfos := make([]deploymentInfo, 0)
	if err := json.Unmarshal(out, &deploymentInfos); err != nil {
		return false, fmt.Errorf("failed to unmarshal deployment list call: %v", err)
	}

	log.Printf("found %v deployments: %v", len(deploymentInfos), deploymentInfos)

	for _, d := range deploymentInfos {
		if d.Name == name {
			return true, nil
		}
	}
	return false, nil
}
