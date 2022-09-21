import React, { Component } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faEnvelope, faLock } from '@fortawesome/free-solid-svg-icons';
import {faGoogle } from '@fortawesome/free-brands-svg-icons';
import logo from './images/trolley.png';

class Register extends Component {
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
        <div className="card card-outline card-primary mt-5 col-lg-4 col-md-6 col-sm-8 mx-auto">
          <div className="card-header text-center">
            <a href="/index" className="login-header"><img src={logo} width="30px" className="me-3" /><b>Trolley</b></a>
          </div>
          <div className="card-body">
            <p className="login-box-msg text-center">Register a new user</p>
            <p className="login-box-msg text-center">{ errorMessage }</p>
            <form action="register" method="POST">
              <div className="input-group mb-3 was-validated">
                <input type="text" className="form-control" placeholder="First Name" name="first_name" required />
                <div className="input-group-text"><FontAwesomeIcon icon={faUser} /></div>
                {/* <div className="invalid-feedback">Please fill out this field.</div> */}
              </div>
              <div className="input-group mb-3">
                <input type="text" className="form-control" placeholder="Last Name" name="last_name" />
                <div className="input-group-text"><FontAwesomeIcon icon={faUser} /></div>
              </div>
              <div className="input-group mb-3 was-validated">
                <input type="email" className="form-control" placeholder="Email" name="user_email" required />
                <div className="input-group-text"><FontAwesomeIcon icon={faEnvelope} /></div>
              </div>
              <div className="input-group mb-3">
                <input type="text" className="form-control" placeholder="Team Name" name="team_name" />
                <div className="input-group-text"><FontAwesomeIcon icon={faUser} /></div>
              </div>
              <div className="input-group mb-3 was-validated">
                <input type="password" className="form-control" placeholder="Password" name="password" required />
                <div className="input-group-text"><FontAwesomeIcon icon={faLock} /></div>
              </div>
              <div className="input-group mb-3">
                <label className="input-group-text" for="imageFile">Select profile image</label>
                <input type="file" className="form-control" id="imageFile" name="file" accept="image/*" style={{width: '0px'}} />
              </div>
              <div className="row">
                <div className="col-8">
                  <div className="icheck-primary input-group">
                    <input type="checkbox" id="agreeTerms" required />
                    <label className="remember-text ps-1" htmlFor="agreeTerms">
                      I agree to the <a href="#">terms</a>
                    </label>
                  </div>
                </div>
                <div className="col-4">
                  <button type="submit" className="btn btn-primary btn-block">Register</button>
                </div>
              </div>
            </form>
            <div className="social-auth-links text-center mt-2 mb-3">
              <a href="#" className="btn btn-block btn-danger">
                <FontAwesomeIcon icon={faGoogle} /> &nbsp; Sign up using Google
              </a>
            </div>
            <p className="mb-0">
              <a href="login" className="text-center">I already have a user</a>
            </p>
          </div>
        </div>
      </div>
    );
  }
}

export default Register;