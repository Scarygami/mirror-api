(function (global) {

  function Service() {
    var state;
    
    this.setState = function (s) {
      if (!state) {
        state = s;
      } else {
        console.log("State variable already set!");
      }
    };
  }

  global.mirrorService = new Service();
  global.onSignInCallback = function (auth_result) {
    console.log(auth_result);
  };
}(this));