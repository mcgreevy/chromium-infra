// Code generated by svcdec; DO NOT EDIT

package crimson

import (
	proto "github.com/golang/protobuf/proto"
	context "golang.org/x/net/context"
)

type DecoratedCrimson struct {
	// Service is the service to decorate.
	Service CrimsonServer
	// Prelude is called for each method before forwarding the call to Service.
	// If Prelude returns an error, it the call is skipped and the error is
	// processed via the Postlude (if one is defined), or it is returned directly.
	Prelude func(c context.Context, methodName string, req proto.Message) (context.Context, error)
	// Postlude is called for each method after Service has processed the call, or
	// after the Prelude has returned an error. This takes the the Service's
	// response proto (which may be nil) and/or any error. The decorated
	// service will return the response (possibly mutated) and error that Postlude
	// returns.
	Postlude func(c context.Context, methodName string, rsp proto.Message, err error) error
}

func (s *DecoratedCrimson) CreateIPRange(c context.Context, req *IPRange) (rsp *IPRangeStatus, err error) {
	var newCtx context.Context
	if s.Prelude != nil {
		newCtx, err = s.Prelude(c, "CreateIPRange", req)
	}
	if err == nil {
		c = newCtx
		rsp, err = s.Service.CreateIPRange(c, req)
	}
	if s.Postlude != nil {
		err = s.Postlude(c, "CreateIPRange", rsp, err)
	}
	return
}

func (s *DecoratedCrimson) ReadIPRange(c context.Context, req *IPRangeQuery) (rsp *IPRanges, err error) {
	var newCtx context.Context
	if s.Prelude != nil {
		newCtx, err = s.Prelude(c, "ReadIPRange", req)
	}
	if err == nil {
		c = newCtx
		rsp, err = s.Service.ReadIPRange(c, req)
	}
	if s.Postlude != nil {
		err = s.Postlude(c, "ReadIPRange", rsp, err)
	}
	return
}

func (s *DecoratedCrimson) DeleteIPRange(c context.Context, req *IPRangeDeleteList) (rsp *IPRangeStatus, err error) {
	var newCtx context.Context
	if s.Prelude != nil {
		newCtx, err = s.Prelude(c, "DeleteIPRange", req)
	}
	if err == nil {
		c = newCtx
		rsp, err = s.Service.DeleteIPRange(c, req)
	}
	if s.Postlude != nil {
		err = s.Postlude(c, "DeleteIPRange", rsp, err)
	}
	return
}

func (s *DecoratedCrimson) CreateHost(c context.Context, req *HostList) (rsp *HostStatus, err error) {
	var newCtx context.Context
	if s.Prelude != nil {
		newCtx, err = s.Prelude(c, "CreateHost", req)
	}
	if err == nil {
		c = newCtx
		rsp, err = s.Service.CreateHost(c, req)
	}
	if s.Postlude != nil {
		err = s.Postlude(c, "CreateHost", rsp, err)
	}
	return
}

func (s *DecoratedCrimson) ReadHost(c context.Context, req *HostQuery) (rsp *HostList, err error) {
	var newCtx context.Context
	if s.Prelude != nil {
		newCtx, err = s.Prelude(c, "ReadHost", req)
	}
	if err == nil {
		c = newCtx
		rsp, err = s.Service.ReadHost(c, req)
	}
	if s.Postlude != nil {
		err = s.Postlude(c, "ReadHost", rsp, err)
	}
	return
}

func (s *DecoratedCrimson) DeleteHost(c context.Context, req *HostDeleteList) (rsp *HostStatus, err error) {
	var newCtx context.Context
	if s.Prelude != nil {
		newCtx, err = s.Prelude(c, "DeleteHost", req)
	}
	if err == nil {
		c = newCtx
		rsp, err = s.Service.DeleteHost(c, req)
	}
	if s.Postlude != nil {
		err = s.Postlude(c, "DeleteHost", rsp, err)
	}
	return
}
