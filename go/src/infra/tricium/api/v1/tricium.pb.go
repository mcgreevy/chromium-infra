// Code generated by protoc-gen-go.
// source: infra/tricium/api/v1/tricium.proto
// DO NOT EDIT!

package tricium

import prpc "github.com/luci/luci-go/grpc/prpc"

import proto "github.com/golang/protobuf/proto"
import fmt "fmt"
import math "math"

import (
	context "golang.org/x/net/context"
	grpc "google.golang.org/grpc"
)

// Reference imports to suppress errors if they are not otherwise used.
var _ = proto.Marshal
var _ = fmt.Errorf
var _ = math.Inf

type ErrorCode int32

const (
	ErrorCode_SUCCESS         ErrorCode = 0
	ErrorCode_TRICIUM_ERROR   ErrorCode = 1
	ErrorCode_UNKNOWN_PROJECT ErrorCode = 2
	ErrorCode_UNKNOWN_GITREF  ErrorCode = 3
)

var ErrorCode_name = map[int32]string{
	0: "SUCCESS",
	1: "TRICIUM_ERROR",
	2: "UNKNOWN_PROJECT",
	3: "UNKNOWN_GITREF",
}
var ErrorCode_value = map[string]int32{
	"SUCCESS":         0,
	"TRICIUM_ERROR":   1,
	"UNKNOWN_PROJECT": 2,
	"UNKNOWN_GITREF":  3,
}

func (x ErrorCode) String() string {
	return proto.EnumName(ErrorCode_name, int32(x))
}
func (ErrorCode) EnumDescriptor() ([]byte, []int) { return fileDescriptor2, []int{0} }

// TriciumRequest contains the details needed for an analysis request.
type TriciumRequest struct {
	// Name of the project hosting the paths listed in the request. The name
	// should map to the project name as it is connected to Tricium.
	Project string `protobuf:"bytes,1,opt,name=project" json:"project,omitempty"`
	GitRef  string `protobuf:"bytes,2,opt,name=git_ref,json=gitRef" json:"git_ref,omitempty"`
	// Paths to analyze in the project. Listed from the root of the Git
	// repository.
	Paths []string `protobuf:"bytes,3,rep,name=paths" json:"paths,omitempty"`
}

func (m *TriciumRequest) Reset()                    { *m = TriciumRequest{} }
func (m *TriciumRequest) String() string            { return proto.CompactTextString(m) }
func (*TriciumRequest) ProtoMessage()               {}
func (*TriciumRequest) Descriptor() ([]byte, []int) { return fileDescriptor2, []int{0} }

func (m *TriciumRequest) GetProject() string {
	if m != nil {
		return m.Project
	}
	return ""
}

func (m *TriciumRequest) GetGitRef() string {
	if m != nil {
		return m.GitRef
	}
	return ""
}

func (m *TriciumRequest) GetPaths() []string {
	if m != nil {
		return m.Paths
	}
	return nil
}

type TriciumResponse struct {
	ErrorCode ErrorCode `protobuf:"varint,1,opt,name=error_code,json=errorCode,enum=tricium.ErrorCode" json:"error_code,omitempty"`
	// Optional error message with more details.
	ErrorMessage string `protobuf:"bytes,2,opt,name=error_message,json=errorMessage" json:"error_message,omitempty"`
	// ID of the run started for this request. This ID can be used to track
	// progress and find results.
	RunId string `protobuf:"bytes,3,opt,name=run_id,json=runId" json:"run_id,omitempty"`
}

func (m *TriciumResponse) Reset()                    { *m = TriciumResponse{} }
func (m *TriciumResponse) String() string            { return proto.CompactTextString(m) }
func (*TriciumResponse) ProtoMessage()               {}
func (*TriciumResponse) Descriptor() ([]byte, []int) { return fileDescriptor2, []int{1} }

func (m *TriciumResponse) GetErrorCode() ErrorCode {
	if m != nil {
		return m.ErrorCode
	}
	return ErrorCode_SUCCESS
}

func (m *TriciumResponse) GetErrorMessage() string {
	if m != nil {
		return m.ErrorMessage
	}
	return ""
}

func (m *TriciumResponse) GetRunId() string {
	if m != nil {
		return m.RunId
	}
	return ""
}

func init() {
	proto.RegisterType((*TriciumRequest)(nil), "tricium.TriciumRequest")
	proto.RegisterType((*TriciumResponse)(nil), "tricium.TriciumResponse")
	proto.RegisterEnum("tricium.ErrorCode", ErrorCode_name, ErrorCode_value)
}

// Reference imports to suppress errors if they are not otherwise used.
var _ context.Context
var _ grpc.ClientConn

// This is a compile-time assertion to ensure that this generated file
// is compatible with the grpc package it is being compiled against.
const _ = grpc.SupportPackageIsVersion4

// Client API for Tricium service

type TriciumClient interface {
	// Analyze requests analysis of a list of paths.
	//
	// An analysis request for a list of paths in a project connected to Tricium
	// via the Tricium configuration. On success, the ID of the resulting run is
	// returned.
	Analyze(ctx context.Context, in *TriciumRequest, opts ...grpc.CallOption) (*TriciumResponse, error)
}
type triciumPRPCClient struct {
	client *prpc.Client
}

func NewTriciumPRPCClient(client *prpc.Client) TriciumClient {
	return &triciumPRPCClient{client}
}

func (c *triciumPRPCClient) Analyze(ctx context.Context, in *TriciumRequest, opts ...grpc.CallOption) (*TriciumResponse, error) {
	out := new(TriciumResponse)
	err := c.client.Call(ctx, "tricium.Tricium", "Analyze", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

type triciumClient struct {
	cc *grpc.ClientConn
}

func NewTriciumClient(cc *grpc.ClientConn) TriciumClient {
	return &triciumClient{cc}
}

func (c *triciumClient) Analyze(ctx context.Context, in *TriciumRequest, opts ...grpc.CallOption) (*TriciumResponse, error) {
	out := new(TriciumResponse)
	err := grpc.Invoke(ctx, "/tricium.Tricium/Analyze", in, out, c.cc, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

// Server API for Tricium service

type TriciumServer interface {
	// Analyze requests analysis of a list of paths.
	//
	// An analysis request for a list of paths in a project connected to Tricium
	// via the Tricium configuration. On success, the ID of the resulting run is
	// returned.
	Analyze(context.Context, *TriciumRequest) (*TriciumResponse, error)
}

func RegisterTriciumServer(s prpc.Registrar, srv TriciumServer) {
	s.RegisterService(&_Tricium_serviceDesc, srv)
}

func _Tricium_Analyze_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(TriciumRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(TriciumServer).Analyze(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/tricium.Tricium/Analyze",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(TriciumServer).Analyze(ctx, req.(*TriciumRequest))
	}
	return interceptor(ctx, in, info, handler)
}

var _Tricium_serviceDesc = grpc.ServiceDesc{
	ServiceName: "tricium.Tricium",
	HandlerType: (*TriciumServer)(nil),
	Methods: []grpc.MethodDesc{
		{
			MethodName: "Analyze",
			Handler:    _Tricium_Analyze_Handler,
		},
	},
	Streams:  []grpc.StreamDesc{},
	Metadata: "infra/tricium/api/v1/tricium.proto",
}

func init() { proto.RegisterFile("infra/tricium/api/v1/tricium.proto", fileDescriptor2) }

var fileDescriptor2 = []byte{
	// 312 bytes of a gzipped FileDescriptorProto
	0x1f, 0x8b, 0x08, 0x00, 0x00, 0x09, 0x6e, 0x88, 0x02, 0xff, 0x64, 0x91, 0x41, 0x4f, 0xc2, 0x40,
	0x10, 0x85, 0x2d, 0x0d, 0x34, 0x1d, 0x05, 0xea, 0xa8, 0xa1, 0xf1, 0x44, 0xf0, 0x42, 0x3c, 0x40,
	0xc0, 0xab, 0x17, 0xd3, 0x54, 0x52, 0x0d, 0x60, 0x96, 0x12, 0xe3, 0xa9, 0xa9, 0x74, 0xc0, 0x35,
	0xd2, 0xad, 0xbb, 0x5b, 0x13, 0x3d, 0xf9, 0xd3, 0x8d, 0x2d, 0x25, 0x31, 0xde, 0xe6, 0xbd, 0x2f,
	0xfb, 0x76, 0xe7, 0x2d, 0xf4, 0x78, 0xba, 0x96, 0xf1, 0x50, 0x4b, 0xbe, 0xe2, 0xf9, 0x76, 0x18,
	0x67, 0x7c, 0xf8, 0x31, 0xaa, 0xe4, 0x20, 0x93, 0x42, 0x0b, 0xb4, 0x76, 0xb2, 0xf7, 0x04, 0xad,
	0xb0, 0x1c, 0x19, 0xbd, 0xe7, 0xa4, 0x34, 0xba, 0x60, 0x65, 0x52, 0xbc, 0xd2, 0x4a, 0xbb, 0x46,
	0xd7, 0xe8, 0xdb, 0xac, 0x92, 0xd8, 0x01, 0x6b, 0xc3, 0x75, 0x24, 0x69, 0xed, 0xd6, 0x0a, 0xd2,
	0xd8, 0x70, 0xcd, 0x68, 0x8d, 0xa7, 0x50, 0xcf, 0x62, 0xfd, 0xa2, 0x5c, 0xb3, 0x6b, 0xf6, 0x6d,
	0x56, 0x8a, 0xde, 0xb7, 0x01, 0xed, 0x7d, 0xb6, 0xca, 0x44, 0xaa, 0x08, 0x47, 0x00, 0x24, 0xa5,
	0x90, 0xd1, 0x4a, 0x24, 0x54, 0xe4, 0xb7, 0xc6, 0x38, 0xa8, 0xde, 0xe6, 0xff, 0x22, 0x4f, 0x24,
	0xc4, 0x6c, 0xaa, 0x46, 0xbc, 0x80, 0x66, 0x79, 0x64, 0x4b, 0x4a, 0xc5, 0x1b, 0xda, 0xdd, 0x7d,
	0x54, 0x98, 0xd3, 0xd2, 0xc3, 0x33, 0x68, 0xc8, 0x3c, 0x8d, 0x78, 0xe2, 0x9a, 0x05, 0xad, 0xcb,
	0x3c, 0x0d, 0x92, 0xcb, 0x10, 0xec, 0x7d, 0x26, 0x1e, 0x82, 0xb5, 0x58, 0x7a, 0x9e, 0xbf, 0x58,
	0x38, 0x07, 0x78, 0x0c, 0xcd, 0x90, 0x05, 0x5e, 0xb0, 0x9c, 0x46, 0x3e, 0x63, 0x73, 0xe6, 0x18,
	0x78, 0x02, 0xed, 0xe5, 0xec, 0x7e, 0x36, 0x7f, 0x9c, 0x45, 0x0f, 0x6c, 0x7e, 0xe7, 0x7b, 0xa1,
	0x53, 0x43, 0x84, 0x56, 0x65, 0x4e, 0x82, 0x90, 0xf9, 0xb7, 0x8e, 0x39, 0x9e, 0x80, 0xb5, 0xdb,
	0x0b, 0xaf, 0xc1, 0xba, 0x49, 0xe3, 0xb7, 0xcf, 0x2f, 0xc2, 0xce, 0x7e, 0x8d, 0xbf, 0x85, 0x9e,
	0xbb, 0xff, 0x41, 0xd9, 0xc6, 0x73, 0xa3, 0xf8, 0x8c, 0xab, 0x9f, 0x00, 0x00, 0x00, 0xff, 0xff,
	0xd3, 0x3c, 0xb3, 0xc7, 0xb2, 0x01, 0x00, 0x00,
}