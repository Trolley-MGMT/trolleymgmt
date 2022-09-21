import React, { Component } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEnvelope, faLock } from '@fortawesome/free-solid-svg-icons';
import {faGoogle } from '@fortawesome/free-brands-svg-icons';
import logo from './images/trolley.png';

class Login extends Component {
  render() {
    let errorMessage = '';
    if (document.getElementById('error').textContent == '{{ error_message|default("")|tojson }}') {
      //errorMessage = 'Debug mode: error messages will show up here';
    } else {
      errorMessage = document.getElementById('error').textContent;
      errorMessage = errorMessage.substring(1, errorMessage.length - 1);
    }
    return(
      <div className="row">
        <div className="card card-outline card-primary col-lg-4 col-md-6 col-sm-8 mx-auto">
          <div className="card-header text-center">
            <a href="/index" className="login-header"><img src={logo} width="30px" className="me-3" /><b>Trolley</b></a>
          </div>
          <div className="card-body">
            <p className="login-box-msg text-center">Sign in to start your session</p>
            <p className="login-box-msg text-center">{ errorMessage }</p>
            <form action="login" method="POST">
              <div className="input-group was-validated mb-3">
                <input type="email" className="form-control" placeholder="Email" name="user_email" required />
                <div className="input-group-text"><FontAwesomeIcon icon={faEnvelope} /></div>
              </div>
              <div className="input-group was-validated mb-3">
                <input type="password" className="form-control" placeholder="Password" name="user_password" required />
                <div className="input-group-text"><FontAwesomeIcon icon={faLock} /></div>
              </div>
              <div className="row">
                <div className="col-8">
                  <div className="icheck-primary input-group">
                    <input type="checkbox" id="remember" />
                    <label className="remember-text ps-1" htmlFor="remember">
                      Remember Me
                    </label>
                  </div>
                </div>
                <div className="col-4">
                    <button type="submit" className="btn btn-primary btn-block">Sign In</button>
                </div>
              </div>
            </form>
            <div className="social-auth-links text-center mt-2 mb-3">
                <a href="#" className="btn btn-block btn-danger">
                    <FontAwesomeIcon icon={faGoogle} /> &nbsp; Sign in using Google
                </a>
            </div>
            <p className="mb-0">
              <a href="/register" class="text-center">Register a new user</a>
            </p>
          </div>
        </div>
      </div>
    );
  }
}

export default Login;