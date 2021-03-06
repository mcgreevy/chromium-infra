package som

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/luci/luci-go/appengine/gaetesting"
	"github.com/luci/luci-go/common/logging"
	"github.com/luci/luci-go/common/logging/gologger"
	"github.com/luci/luci-go/server/auth"
	"github.com/luci/luci-go/server/auth/authtest"

	gerrit "github.com/andygrunwald/go-gerrit"
	. "github.com/smartystreets/goconvey/convey"
)

func TestGerritClient(t *testing.T) {
	testMux := http.NewServeMux()
	testServer := httptest.NewServer(testMux)

	Convey("get client", t, func() {
		c := gaetesting.TestingContext()
		c = authtest.MockAuthConfig(c)
		authState := &authtest.FakeState{
			Identity: "user:user@example.com",
		}
		c = auth.WithState(c, authState)

		client, err := getGerritClient(c, testServer.URL)
		So(err, ShouldBeNil)
		So(client, ShouldNotBeNil)
	})

	Convey("create CL", t, func() {
		c := gaetesting.TestingContext()
		c = gologger.StdConfig.Use(c)
		c = authtest.MockAuthConfig(c)
		authState := &authtest.FakeState{
			Identity: "user:user@example.com",
		}
		c = auth.WithState(c, authState)

		created, uploaded, published := false, false, false

		testMux.HandleFunc("/a/changes/", func(w http.ResponseWriter, r *http.Request) {
			logging.Infof(c, "%s: %v", r.Method, r.URL.Path)
			switch r.Method {
			case "POST":
				if strings.HasSuffix(r.URL.Path, ":publish") {
					published = true
					break
				}
				marshalled, _ := json.Marshal(&gerrit.ChangeInfo{
					Project:  "project",
					Branch:   "branch",
					Subject:  "subject",
					Status:   "DRAFT",
					Topic:    "",
					ChangeID: "1234",
				})
				fmt.Fprintf(w, ")]}'\n%s", string(marshalled))
				created = true
				break
			case "PUT":
				w.WriteHeader(http.StatusOK)
				uploaded = true
				break
			default:
				w.WriteHeader(http.StatusBadRequest)
			}
		})

		client, err := getGerritClient(c, testServer.URL)
		So(err, ShouldBeNil)

		fileContents := map[string]string{
			"test_file.txt": "file contents",
		}
		changeID, err := createCL(client, "project", "branch", "subject", fileContents)
		So(err, ShouldBeNil)
		So(created, ShouldBeTrue)
		So(uploaded, ShouldBeTrue)
		So(published, ShouldBeTrue)
		So(changeID, ShouldEqual, "1234")
	})
}
