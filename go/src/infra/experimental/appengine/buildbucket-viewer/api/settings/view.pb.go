// Code generated by protoc-gen-go.
// source: infra/experimental/appengine/buildbucket-viewer/api/settings/view.proto
// DO NOT EDIT!

package settings

import proto "github.com/golang/protobuf/proto"
import fmt "fmt"
import math "math"
import google_protobuf "github.com/golang/protobuf/ptypes/duration"

// Reference imports to suppress errors if they are not otherwise used.
var _ = proto.Marshal
var _ = fmt.Errorf
var _ = math.Inf

// Sentinel for tag values that can be calculated.
type View_Tag_CalculatedValue int32

const (
	// Empty value (default).
	View_Tag_EMPTY View_Tag_CalculatedValue = 0
	// The latest paladin build's master build ID.
	View_Tag_LATEST_PALADIN_BUILD View_Tag_CalculatedValue = 1
	// The latest PFQ build's master build ID.
	View_Tag_LATEST_PFQ_BUILD View_Tag_CalculatedValue = 2
	// The latest Canary build's master build ID.
	View_Tag_LATEST_CANARY_BUILD View_Tag_CalculatedValue = 3
	// The latest Release build's master build ID.
	View_Tag_LATEST_RELEASE_BUILD View_Tag_CalculatedValue = 4
	// The latest Toolchain build's master build ID.
	View_Tag_LATEST_TOOLCHAIN_BUILD View_Tag_CalculatedValue = 5
)

var View_Tag_CalculatedValue_name = map[int32]string{
	0: "EMPTY",
	1: "LATEST_PALADIN_BUILD",
	2: "LATEST_PFQ_BUILD",
	3: "LATEST_CANARY_BUILD",
	4: "LATEST_RELEASE_BUILD",
	5: "LATEST_TOOLCHAIN_BUILD",
}
var View_Tag_CalculatedValue_value = map[string]int32{
	"EMPTY":                  0,
	"LATEST_PALADIN_BUILD":   1,
	"LATEST_PFQ_BUILD":       2,
	"LATEST_CANARY_BUILD":    3,
	"LATEST_RELEASE_BUILD":   4,
	"LATEST_TOOLCHAIN_BUILD": 5,
}

func (x View_Tag_CalculatedValue) String() string {
	return proto.EnumName(View_Tag_CalculatedValue_name, int32(x))
}
func (View_Tag_CalculatedValue) EnumDescriptor() ([]byte, []int) {
	return fileDescriptor1, []int{1, 0, 0}
}

// Constrain to the specified Result.
type View_Section_Result int32

const (
	View_Section_ALL                      View_Section_Result = 0
	View_Section_SUCCESS                  View_Section_Result = 1
	View_Section_CANCELED                 View_Section_Result = 2
	View_Section_FAILURE                  View_Section_Result = 3
	View_Section_BUILDBUCKET_FAILURE      View_Section_Result = 4
	View_Section_BUILD_FAILURE            View_Section_Result = 5
	View_Section_INFRA_FAILURE            View_Section_Result = 6
	View_Section_INVALID_BUILD_DEFINITION View_Section_Result = 7
)

var View_Section_Result_name = map[int32]string{
	0: "ALL",
	1: "SUCCESS",
	2: "CANCELED",
	3: "FAILURE",
	4: "BUILDBUCKET_FAILURE",
	5: "BUILD_FAILURE",
	6: "INFRA_FAILURE",
	7: "INVALID_BUILD_DEFINITION",
}
var View_Section_Result_value = map[string]int32{
	"ALL":                      0,
	"SUCCESS":                  1,
	"CANCELED":                 2,
	"FAILURE":                  3,
	"BUILDBUCKET_FAILURE":      4,
	"BUILD_FAILURE":            5,
	"INFRA_FAILURE":            6,
	"INVALID_BUILD_DEFINITION": 7,
}

func (x View_Section_Result) String() string {
	return proto.EnumName(View_Section_Result_name, int32(x))
}
func (View_Section_Result) EnumDescriptor() ([]byte, []int) { return fileDescriptor1, []int{1, 1, 0} }

type View_Section_Show_Info int32

const (
	View_Section_Show_NONE           View_Section_Show_Info = 0
	View_Section_Show_STATUS         View_Section_Show_Info = 1
	View_Section_Show_FAILURE_REASON View_Section_Show_Info = 2
)

var View_Section_Show_Info_name = map[int32]string{
	0: "NONE",
	1: "STATUS",
	2: "FAILURE_REASON",
}
var View_Section_Show_Info_value = map[string]int32{
	"NONE":           0,
	"STATUS":         1,
	"FAILURE_REASON": 2,
}

func (x View_Section_Show_Info) String() string {
	return proto.EnumName(View_Section_Show_Info_name, int32(x))
}
func (View_Section_Show_Info) EnumDescriptor() ([]byte, []int) {
	return fileDescriptor1, []int{1, 1, 0, 0}
}

// ProjectConfig is the project-specific configuration settings for this
// service.
type ProjectConfig struct {
	// The title of this project, as it shows up in "All Views".
	Title string `protobuf:"bytes,1,opt,name=title" json:"title,omitempty"`
	// Map of view entries for this project.
	View map[string]*View `protobuf:"bytes,2,rep,name=view" json:"view,omitempty" protobuf_key:"bytes,1,opt,name=key" protobuf_val:"bytes,2,opt,name=value"`
}

func (m *ProjectConfig) Reset()                    { *m = ProjectConfig{} }
func (m *ProjectConfig) String() string            { return proto.CompactTextString(m) }
func (*ProjectConfig) ProtoMessage()               {}
func (*ProjectConfig) Descriptor() ([]byte, []int) { return fileDescriptor1, []int{0} }

func (m *ProjectConfig) GetTitle() string {
	if m != nil {
		return m.Title
	}
	return ""
}

func (m *ProjectConfig) GetView() map[string]*View {
	if m != nil {
		return m.View
	}
	return nil
}

// View defines a specific build set view.
type View struct {
	// The view title. If empty, a title will be generated.
	Title string `protobuf:"bytes,1,opt,name=title" json:"title,omitempty"`
	// The set of BuildBucket queries to represent in this view.
	Section []*View_Section `protobuf:"bytes,2,rep,name=section" json:"section,omitempty"`
	// If >0, make this view automatically refresh itself every interval.
	RefreshInterval *google_protobuf.Duration `protobuf:"bytes,3,opt,name=refresh_interval,json=refreshInterval" json:"refresh_interval,omitempty"`
}

func (m *View) Reset()                    { *m = View{} }
func (m *View) String() string            { return proto.CompactTextString(m) }
func (*View) ProtoMessage()               {}
func (*View) Descriptor() ([]byte, []int) { return fileDescriptor1, []int{1} }

func (m *View) GetTitle() string {
	if m != nil {
		return m.Title
	}
	return ""
}

func (m *View) GetSection() []*View_Section {
	if m != nil {
		return m.Section
	}
	return nil
}

func (m *View) GetRefreshInterval() *google_protobuf.Duration {
	if m != nil {
		return m.RefreshInterval
	}
	return nil
}

// Represents a "key:value" BuildBucket tag.
//
// The <value> may be specified as a "CalculatedValue", in which case it will
// be calculated and substituted at query time.
type View_Tag struct {
	// The tag's key.
	Key string `protobuf:"bytes,1,opt,name=key" json:"key,omitempty"`
	// Types that are valid to be assigned to Tagval:
	//	*View_Tag_Value
	//	*View_Tag_Calc
	Tagval isView_Tag_Tagval `protobuf_oneof:"tagval"`
}

func (m *View_Tag) Reset()                    { *m = View_Tag{} }
func (m *View_Tag) String() string            { return proto.CompactTextString(m) }
func (*View_Tag) ProtoMessage()               {}
func (*View_Tag) Descriptor() ([]byte, []int) { return fileDescriptor1, []int{1, 0} }

type isView_Tag_Tagval interface {
	isView_Tag_Tagval()
}

type View_Tag_Value struct {
	Value string `protobuf:"bytes,2,opt,name=value,oneof"`
}
type View_Tag_Calc struct {
	Calc View_Tag_CalculatedValue `protobuf:"varint,3,opt,name=calc,enum=settings.View_Tag_CalculatedValue,oneof"`
}

func (*View_Tag_Value) isView_Tag_Tagval() {}
func (*View_Tag_Calc) isView_Tag_Tagval()  {}

func (m *View_Tag) GetTagval() isView_Tag_Tagval {
	if m != nil {
		return m.Tagval
	}
	return nil
}

func (m *View_Tag) GetKey() string {
	if m != nil {
		return m.Key
	}
	return ""
}

func (m *View_Tag) GetValue() string {
	if x, ok := m.GetTagval().(*View_Tag_Value); ok {
		return x.Value
	}
	return ""
}

func (m *View_Tag) GetCalc() View_Tag_CalculatedValue {
	if x, ok := m.GetTagval().(*View_Tag_Calc); ok {
		return x.Calc
	}
	return View_Tag_EMPTY
}

// XXX_OneofFuncs is for the internal use of the proto package.
func (*View_Tag) XXX_OneofFuncs() (func(msg proto.Message, b *proto.Buffer) error, func(msg proto.Message, tag, wire int, b *proto.Buffer) (bool, error), func(msg proto.Message) (n int), []interface{}) {
	return _View_Tag_OneofMarshaler, _View_Tag_OneofUnmarshaler, _View_Tag_OneofSizer, []interface{}{
		(*View_Tag_Value)(nil),
		(*View_Tag_Calc)(nil),
	}
}

func _View_Tag_OneofMarshaler(msg proto.Message, b *proto.Buffer) error {
	m := msg.(*View_Tag)
	// tagval
	switch x := m.Tagval.(type) {
	case *View_Tag_Value:
		b.EncodeVarint(2<<3 | proto.WireBytes)
		b.EncodeStringBytes(x.Value)
	case *View_Tag_Calc:
		b.EncodeVarint(3<<3 | proto.WireVarint)
		b.EncodeVarint(uint64(x.Calc))
	case nil:
	default:
		return fmt.Errorf("View_Tag.Tagval has unexpected type %T", x)
	}
	return nil
}

func _View_Tag_OneofUnmarshaler(msg proto.Message, tag, wire int, b *proto.Buffer) (bool, error) {
	m := msg.(*View_Tag)
	switch tag {
	case 2: // tagval.value
		if wire != proto.WireBytes {
			return true, proto.ErrInternalBadWireType
		}
		x, err := b.DecodeStringBytes()
		m.Tagval = &View_Tag_Value{x}
		return true, err
	case 3: // tagval.calc
		if wire != proto.WireVarint {
			return true, proto.ErrInternalBadWireType
		}
		x, err := b.DecodeVarint()
		m.Tagval = &View_Tag_Calc{View_Tag_CalculatedValue(x)}
		return true, err
	default:
		return false, nil
	}
}

func _View_Tag_OneofSizer(msg proto.Message) (n int) {
	m := msg.(*View_Tag)
	// tagval
	switch x := m.Tagval.(type) {
	case *View_Tag_Value:
		n += proto.SizeVarint(2<<3 | proto.WireBytes)
		n += proto.SizeVarint(uint64(len(x.Value)))
		n += len(x.Value)
	case *View_Tag_Calc:
		n += proto.SizeVarint(3<<3 | proto.WireVarint)
		n += proto.SizeVarint(uint64(x.Calc))
	case nil:
	default:
		panic(fmt.Sprintf("proto: unexpected type %T in oneof", x))
	}
	return n
}

// A Section is an individual BuildBucket query that will be represented as
// a section in this view.
type View_Section struct {
	// The name of this section. If omitted, one will be generated.
	Name string `protobuf:"bytes,1,opt,name=name" json:"name,omitempty"`
	// (Required) The BuildBucket bucket to query.
	Bucket []string `protobuf:"bytes,2,rep,name=bucket" json:"bucket,omitempty"`
	// BuildBucket tags to query on. Will be constructed as "key:value".
	Tag []*View_Tag `protobuf:"bytes,3,rep,name=tag" json:"tag,omitempty"`
	// The BuildBucket tag whose value should be used as the title for each
	// build entry in this view. If empty, the title will be generated.
	TitleTag []string `protobuf:"bytes,4,rep,name=title_tag,json=titleTag" json:"title_tag,omitempty"`
	// The BuildBucket tag keys to use to sort builds in this view. If omitted,
	// the BuildBucket ID will be used.
	SortTag []string `protobuf:"bytes,5,rep,name=sort_tag,json=sortTag" json:"sort_tag,omitempty"`
	// Tags whose values should be shown when rendering the view.
	Show   []*View_Section_Show `protobuf:"bytes,6,rep,name=show" json:"show,omitempty"`
	Result View_Section_Result  `protobuf:"varint,8,opt,name=result,enum=settings.View_Section_Result" json:"result,omitempty"`
	// The maximum number of builds to retrieve. If empty, builds will be pulled
	// up to an app-defined maximum.
	MaxBuilds int32 `protobuf:"varint,9,opt,name=max_builds,json=maxBuilds" json:"max_builds,omitempty"`
}

func (m *View_Section) Reset()                    { *m = View_Section{} }
func (m *View_Section) String() string            { return proto.CompactTextString(m) }
func (*View_Section) ProtoMessage()               {}
func (*View_Section) Descriptor() ([]byte, []int) { return fileDescriptor1, []int{1, 1} }

func (m *View_Section) GetName() string {
	if m != nil {
		return m.Name
	}
	return ""
}

func (m *View_Section) GetBucket() []string {
	if m != nil {
		return m.Bucket
	}
	return nil
}

func (m *View_Section) GetTag() []*View_Tag {
	if m != nil {
		return m.Tag
	}
	return nil
}

func (m *View_Section) GetTitleTag() []string {
	if m != nil {
		return m.TitleTag
	}
	return nil
}

func (m *View_Section) GetSortTag() []string {
	if m != nil {
		return m.SortTag
	}
	return nil
}

func (m *View_Section) GetShow() []*View_Section_Show {
	if m != nil {
		return m.Show
	}
	return nil
}

func (m *View_Section) GetResult() View_Section_Result {
	if m != nil {
		return m.Result
	}
	return View_Section_ALL
}

func (m *View_Section) GetMaxBuilds() int32 {
	if m != nil {
		return m.MaxBuilds
	}
	return 0
}

// Information to show in the build's description.
type View_Section_Show struct {
	// Types that are valid to be assigned to What:
	//	*View_Section_Show_Tag
	//	*View_Section_Show_Info_
	What isView_Section_Show_What `protobuf_oneof:"what"`
}

func (m *View_Section_Show) Reset()                    { *m = View_Section_Show{} }
func (m *View_Section_Show) String() string            { return proto.CompactTextString(m) }
func (*View_Section_Show) ProtoMessage()               {}
func (*View_Section_Show) Descriptor() ([]byte, []int) { return fileDescriptor1, []int{1, 1, 0} }

type isView_Section_Show_What interface {
	isView_Section_Show_What()
}

type View_Section_Show_Tag struct {
	Tag string `protobuf:"bytes,1,opt,name=tag,oneof"`
}
type View_Section_Show_Info_ struct {
	Info View_Section_Show_Info `protobuf:"varint,2,opt,name=info,enum=settings.View_Section_Show_Info,oneof"`
}

func (*View_Section_Show_Tag) isView_Section_Show_What()   {}
func (*View_Section_Show_Info_) isView_Section_Show_What() {}

func (m *View_Section_Show) GetWhat() isView_Section_Show_What {
	if m != nil {
		return m.What
	}
	return nil
}

func (m *View_Section_Show) GetTag() string {
	if x, ok := m.GetWhat().(*View_Section_Show_Tag); ok {
		return x.Tag
	}
	return ""
}

func (m *View_Section_Show) GetInfo() View_Section_Show_Info {
	if x, ok := m.GetWhat().(*View_Section_Show_Info_); ok {
		return x.Info
	}
	return View_Section_Show_NONE
}

// XXX_OneofFuncs is for the internal use of the proto package.
func (*View_Section_Show) XXX_OneofFuncs() (func(msg proto.Message, b *proto.Buffer) error, func(msg proto.Message, tag, wire int, b *proto.Buffer) (bool, error), func(msg proto.Message) (n int), []interface{}) {
	return _View_Section_Show_OneofMarshaler, _View_Section_Show_OneofUnmarshaler, _View_Section_Show_OneofSizer, []interface{}{
		(*View_Section_Show_Tag)(nil),
		(*View_Section_Show_Info_)(nil),
	}
}

func _View_Section_Show_OneofMarshaler(msg proto.Message, b *proto.Buffer) error {
	m := msg.(*View_Section_Show)
	// what
	switch x := m.What.(type) {
	case *View_Section_Show_Tag:
		b.EncodeVarint(1<<3 | proto.WireBytes)
		b.EncodeStringBytes(x.Tag)
	case *View_Section_Show_Info_:
		b.EncodeVarint(2<<3 | proto.WireVarint)
		b.EncodeVarint(uint64(x.Info))
	case nil:
	default:
		return fmt.Errorf("View_Section_Show.What has unexpected type %T", x)
	}
	return nil
}

func _View_Section_Show_OneofUnmarshaler(msg proto.Message, tag, wire int, b *proto.Buffer) (bool, error) {
	m := msg.(*View_Section_Show)
	switch tag {
	case 1: // what.tag
		if wire != proto.WireBytes {
			return true, proto.ErrInternalBadWireType
		}
		x, err := b.DecodeStringBytes()
		m.What = &View_Section_Show_Tag{x}
		return true, err
	case 2: // what.info
		if wire != proto.WireVarint {
			return true, proto.ErrInternalBadWireType
		}
		x, err := b.DecodeVarint()
		m.What = &View_Section_Show_Info_{View_Section_Show_Info(x)}
		return true, err
	default:
		return false, nil
	}
}

func _View_Section_Show_OneofSizer(msg proto.Message) (n int) {
	m := msg.(*View_Section_Show)
	// what
	switch x := m.What.(type) {
	case *View_Section_Show_Tag:
		n += proto.SizeVarint(1<<3 | proto.WireBytes)
		n += proto.SizeVarint(uint64(len(x.Tag)))
		n += len(x.Tag)
	case *View_Section_Show_Info_:
		n += proto.SizeVarint(2<<3 | proto.WireVarint)
		n += proto.SizeVarint(uint64(x.Info))
	case nil:
	default:
		panic(fmt.Sprintf("proto: unexpected type %T in oneof", x))
	}
	return n
}

func init() {
	proto.RegisterType((*ProjectConfig)(nil), "settings.ProjectConfig")
	proto.RegisterType((*View)(nil), "settings.View")
	proto.RegisterType((*View_Tag)(nil), "settings.View.Tag")
	proto.RegisterType((*View_Section)(nil), "settings.View.Section")
	proto.RegisterType((*View_Section_Show)(nil), "settings.View.Section.Show")
	proto.RegisterEnum("settings.View_Tag_CalculatedValue", View_Tag_CalculatedValue_name, View_Tag_CalculatedValue_value)
	proto.RegisterEnum("settings.View_Section_Result", View_Section_Result_name, View_Section_Result_value)
	proto.RegisterEnum("settings.View_Section_Show_Info", View_Section_Show_Info_name, View_Section_Show_Info_value)
}

func init() {
	proto.RegisterFile("infra/experimental/appengine/buildbucket-viewer/api/settings/view.proto", fileDescriptor1)
}

var fileDescriptor1 = []byte{
	// 756 bytes of a gzipped FileDescriptorProto
	0x1f, 0x8b, 0x08, 0x00, 0x00, 0x09, 0x6e, 0x88, 0x02, 0xff, 0x7c, 0x53, 0x4d, 0x73, 0x9b, 0x46,
	0x18, 0x16, 0x02, 0x81, 0x78, 0xdd, 0x38, 0x74, 0xeb, 0x71, 0x89, 0xd2, 0x74, 0x54, 0x4d, 0x0e,
	0xbe, 0x14, 0x32, 0xee, 0xa4, 0x93, 0xe9, 0x0d, 0x21, 0x1c, 0x33, 0xa5, 0xc8, 0x5d, 0x90, 0x67,
	0x72, 0x62, 0xd6, 0xf2, 0x0a, 0xd3, 0x60, 0xd0, 0xc0, 0xca, 0x72, 0xfe, 0x43, 0x2f, 0xbd, 0xf4,
	0xd2, 0x73, 0xff, 0x48, 0xff, 0x4f, 0xff, 0x43, 0x67, 0x97, 0x95, 0x9a, 0xa4, 0x71, 0x6f, 0xec,
	0xf3, 0xbc, 0xef, 0xf3, 0x7e, 0x3d, 0xc0, 0xeb, 0xa2, 0x5a, 0x35, 0xc4, 0xa5, 0xf7, 0x6b, 0xda,
	0x14, 0xb7, 0xb4, 0x62, 0xa4, 0x74, 0xc9, 0x7a, 0x4d, 0xab, 0xbc, 0xa8, 0xa8, 0x7b, 0xb5, 0x29,
	0xca, 0xeb, 0xab, 0xcd, 0xf2, 0x2d, 0x65, 0xdf, 0xde, 0x15, 0x74, 0x4b, 0x1b, 0x97, 0xac, 0x0b,
	0xb7, 0xa5, 0x8c, 0x15, 0x55, 0xde, 0xba, 0x1c, 0x73, 0xd6, 0x4d, 0xcd, 0x6a, 0x34, 0xdc, 0x81,
	0xa3, 0xaf, 0xf3, 0xba, 0xce, 0x4b, 0xea, 0x0a, 0xfc, 0x6a, 0xb3, 0x72, 0xaf, 0x37, 0x0d, 0x61,
	0x45, 0x5d, 0x75, 0x91, 0x93, 0x3f, 0x15, 0x78, 0x74, 0xd1, 0xd4, 0xbf, 0xd0, 0x25, 0xf3, 0xeb,
	0x6a, 0x55, 0xe4, 0xe8, 0x08, 0x06, 0xac, 0x60, 0x25, 0xb5, 0x95, 0xb1, 0x72, 0x62, 0xe2, 0xee,
	0x81, 0x5e, 0x82, 0xc6, 0xf5, 0xed, 0xfe, 0x58, 0x3d, 0x39, 0x38, 0xfd, 0xc6, 0xd9, 0x15, 0x70,
	0x3e, 0x48, 0x76, 0x2e, 0x0b, 0xba, 0x0d, 0x2a, 0xd6, 0xbc, 0xc3, 0x22, 0x7c, 0xf4, 0x1a, 0xcc,
	0x3d, 0x84, 0x2c, 0x50, 0xdf, 0xd2, 0x77, 0x52, 0x97, 0x7f, 0xa2, 0xe7, 0x30, 0xb8, 0x23, 0xe5,
	0x86, 0xda, 0xfd, 0xb1, 0x72, 0x72, 0x70, 0x7a, 0xf8, 0xaf, 0x2c, 0xcf, 0xc2, 0x1d, 0xf9, 0x43,
	0xff, 0x95, 0x32, 0xf9, 0xdb, 0x00, 0x8d, 0x63, 0x0f, 0xb4, 0xf7, 0x02, 0x8c, 0x96, 0x2e, 0xf9,
	0x5c, 0xb2, 0xc3, 0xe3, 0x0f, 0xa5, 0x9c, 0xa4, 0x63, 0xf1, 0x2e, 0x0c, 0xcd, 0xc0, 0x6a, 0xe8,
	0xaa, 0xa1, 0xed, 0x4d, 0x56, 0x54, 0x8c, 0x36, 0x77, 0xa4, 0xb4, 0x55, 0xd1, 0xc5, 0x13, 0xa7,
	0xdb, 0x99, 0xb3, 0xdb, 0x99, 0x33, 0x93, 0x3b, 0xc3, 0x8f, 0x65, 0x4a, 0x28, 0x33, 0x46, 0xbf,
	0xf5, 0x41, 0x4d, 0x49, 0xfe, 0x89, 0xd1, 0x8e, 0xdf, 0x1f, 0xcd, 0x3c, 0xef, 0xc9, 0x61, 0xd0,
	0x2b, 0xd0, 0x96, 0xa4, 0x5c, 0x8a, 0x5a, 0x87, 0xa7, 0x93, 0x8f, 0xda, 0x4c, 0x49, 0xee, 0xf8,
	0xa4, 0x5c, 0x6e, 0x4a, 0xc2, 0xe8, 0xf5, 0x25, 0xcf, 0x38, 0xef, 0x61, 0x91, 0x31, 0xf9, 0x43,
	0x81, 0xc7, 0x1f, 0x71, 0xc8, 0x84, 0x41, 0xf0, 0xd3, 0x45, 0xfa, 0xc6, 0xea, 0x21, 0x1b, 0x8e,
	0x22, 0x2f, 0x0d, 0x92, 0x34, 0xbb, 0xf0, 0x22, 0x6f, 0x16, 0xc6, 0xd9, 0x74, 0x11, 0x46, 0x33,
	0x4b, 0x41, 0x47, 0x60, 0xed, 0x98, 0xb3, 0x9f, 0x25, 0xda, 0x47, 0x5f, 0xc2, 0x17, 0x12, 0xf5,
	0xbd, 0xd8, 0xc3, 0x6f, 0x24, 0xa1, 0xbe, 0x27, 0x84, 0x83, 0x28, 0xf0, 0x92, 0x40, 0x32, 0x1a,
	0x1a, 0xc1, 0xb1, 0x64, 0xd2, 0xf9, 0x3c, 0xf2, 0xcf, 0xbd, 0x7d, 0x91, 0xc1, 0x74, 0x08, 0x3a,
	0x23, 0x39, 0xdf, 0xc9, 0x5f, 0x1a, 0x18, 0x72, 0xdd, 0x08, 0x81, 0x56, 0x91, 0xdb, 0xdd, 0xb1,
	0xc4, 0x37, 0x3a, 0x06, 0xbd, 0x73, 0xb1, 0x38, 0x95, 0x89, 0xe5, 0x0b, 0x3d, 0x07, 0x95, 0x91,
	0xdc, 0x56, 0xc5, 0xfd, 0xd0, 0x7f, 0x17, 0x83, 0x39, 0x8d, 0x9e, 0x82, 0x29, 0x4e, 0x9e, 0xf1,
	0x58, 0x4d, 0x08, 0x0c, 0x05, 0xc0, 0xcf, 0xf0, 0x04, 0x86, 0x6d, 0xdd, 0x30, 0xc1, 0x0d, 0x04,
	0x67, 0xf0, 0x37, 0xa7, 0x5c, 0xd0, 0xda, 0x9b, 0x7a, 0x6b, 0xeb, 0x42, 0xfe, 0xe9, 0xa7, 0xed,
	0xe1, 0x24, 0x37, 0xf5, 0x16, 0x8b, 0x40, 0xf4, 0x12, 0xf4, 0x86, 0xb6, 0x9b, 0x92, 0xd9, 0x43,
	0x71, 0xaa, 0x67, 0x0f, 0xa4, 0x60, 0x11, 0x84, 0x65, 0x30, 0x7a, 0x06, 0x70, 0x4b, 0xee, 0x33,
	0xf1, 0xb3, 0xb6, 0xb6, 0x39, 0x56, 0x4e, 0x06, 0xd8, 0xbc, 0x25, 0xf7, 0x53, 0x01, 0x8c, 0x7e,
	0x55, 0x40, 0xe3, 0x45, 0x10, 0xea, 0xa6, 0x55, 0xa4, 0x3b, 0xc4, 0x6c, 0xdf, 0x83, 0x56, 0x54,
	0xab, 0x5a, 0x58, 0xe6, 0xf0, 0x74, 0xfc, 0x3f, 0x3d, 0x3a, 0x61, 0xb5, 0xaa, 0xb9, 0x33, 0x78,
	0xfc, 0xe4, 0x05, 0x68, 0xfc, 0x8d, 0x86, 0xa0, 0xc5, 0xf3, 0x38, 0xb0, 0x7a, 0x08, 0x40, 0x4f,
	0x52, 0x2f, 0x5d, 0x24, 0x96, 0x82, 0x10, 0x1c, 0x9e, 0x79, 0x61, 0xb4, 0xc0, 0x41, 0x86, 0x03,
	0x2f, 0x99, 0xc7, 0x56, 0x7f, 0xaa, 0x83, 0xb6, 0xbd, 0x21, 0x6c, 0xf2, 0xbb, 0x02, 0x7a, 0x37,
	0x00, 0x32, 0x40, 0xf5, 0xa2, 0xc8, 0xea, 0xa1, 0x03, 0x30, 0x92, 0x85, 0xef, 0x07, 0x09, 0x4f,
	0xfe, 0x0c, 0x86, 0xbe, 0x17, 0xfb, 0x41, 0x14, 0x70, 0xcf, 0x1c, 0x80, 0x21, 0xa5, 0x2c, 0x95,
	0x1b, 0x48, 0x1c, 0x7f, 0xba, 0xf0, 0x7f, 0x0c, 0xd2, 0x6c, 0x47, 0x68, 0xe8, 0x73, 0x78, 0x24,
	0x88, 0x3d, 0x34, 0xe0, 0x50, 0x18, 0x9f, 0x61, 0x6f, 0x0f, 0xe9, 0xe8, 0x2b, 0xb0, 0xc3, 0xf8,
	0xd2, 0x8b, 0xc2, 0x59, 0xe7, 0xa1, 0x6c, 0x16, 0x9c, 0x85, 0x71, 0x98, 0x86, 0xf3, 0xd8, 0x32,
	0xae, 0x74, 0xf1, 0xf3, 0x7d, 0xf7, 0x4f, 0x00, 0x00, 0x00, 0xff, 0xff, 0x83, 0x9b, 0xc7, 0xf0,
	0x13, 0x05, 0x00, 0x00,
}
