package step

import (
	"fmt"
	"sort"
	"strconv"
	"strings"

	"golang.org/x/net/context"

	"infra/monitoring/messages"
)

const deviceAffinityText = "Device Affinity: "

// Gets the device affinity of a step.
// TODO(martiniss): Use more structured data. Steps now have logs, named
// "device affinity", which have the number in it. In order to get these logs,
// however, you need to hit the buildbot master again, which makes it extremely
// unperformant. Not sure how to solve this :/
func getDeviceAffinity(step *messages.Step) (bool, int, error) {
	text := strings.TrimSpace(strings.Join(step.Text, ""))
	if strings.HasSuffix(text, "<br/>") {
		text = text[:len(text)-len("<br/>")]
	}
	if len(text) < len(deviceAffinityText)+1 {
		return false, 0, nil
	}

	affinity := text[len(text)-len(deviceAffinityText)-1:]
	if strings.HasPrefix(affinity, deviceAffinityText) {
		num, err := strconv.Atoi(string(affinity[len(affinity)-1]))
		if err != nil {
			return false, 0, err
		}
		return true, num, nil
	}
	return false, 0, nil
}

type deviceFailure struct {
	Builder string
	Devices []int
}

func (p *deviceFailure) Signature() string {
	return fmt.Sprintf("%s/%s", p.Builder, p.devicesStr())
}

// devicesStr is a string representation of the device affinities which have
// failed.
func (p *deviceFailure) devicesStr() string {
	sort.Ints(p.Devices)
	devicesStr := make([]string, len(p.Devices))
	for i, device := range p.Devices {
		devicesStr[i] = strconv.Itoa(device)
	}

	return strings.Join(devicesStr, ", ")
}

func (p *deviceFailure) Kind() string {
	return "perf-device"
}

func (p *deviceFailure) Severity() messages.Severity {
	return messages.InfraFailure
}

func (p *deviceFailure) Title(bses []*messages.BuildStep) string {
	if len(bses) == 0 {
		return fmt.Sprintf("device affinity %s broken", p.devicesStr())
	}

	f := bses[0]
	return fmt.Sprintf("device affinity %s is broken on %s/%s, affecting %d tests", p.devicesStr(), f.Master.Name(), p.Builder, len(bses))
}

// deviceAnalyzer looks for perf device failures.
func deviceAnalyzer(ctx context.Context, failures []*messages.BuildStep) ([]messages.ReasonRaw, []error) {
	if len(failures) == 0 {
		return []messages.ReasonRaw{}, nil
	}

	isStepFailure := make(map[string]bool)
	for _, failure := range failures {
		ok, err := failure.Step.IsOK()
		if err != nil {
			continue
		}

		if !ok {
			isStepFailure[failure.Step.Name] = true
		}
	}

	isAffinityFailure := make(map[string]bool)
	deviceWithPassingTests := map[int]bool{}

	for _, step := range failures[0].Build.Steps {
		recognized, num, err := getDeviceAffinity(&step)
		if err != nil {
			return nil, []error{err}
		}

		if !recognized {
			continue
		}

		isAffinityFailure[step.Name] = true
		if !isStepFailure[step.Name] {
			deviceWithPassingTests[num] = true
		}
	}

	results := make([]messages.ReasonRaw, len(failures))
	deviceHasFailure := map[int]bool{}

	devFailure := &deviceFailure{
		Builder: failures[0].Build.BuilderName,
		Devices: []int{},
	}

	for i, f := range failures {
		if f.Step.Name == "Host Info" {
			results[i] = devFailure
			continue
		}

		recognized, num, _ := getDeviceAffinity(f.Step)

		if recognized && !deviceWithPassingTests[num] {
			deviceHasFailure[num] = true
			// devFailure.Devices might not be fully populated yet, but because of the
			// magic of pointers, this still works.
			results[i] = devFailure
		}
	}

	for device, present := range deviceHasFailure {
		if present {
			devFailure.Devices = append(devFailure.Devices, device)
		}
	}

	return results, nil
}
