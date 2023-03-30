import React from 'react';
import logo from './logo.svg';
import processing from './processing.gif'
import './App.css';

class SelectFile extends React.Component {
  
  constructor(props) {
    super(props);
    this.handleChange = this.handleChange.bind(this);
  }  

  handleChange(e) {
    this.props.onFileChange(e.target.files[0]);
  }

  render() {
    return (
      <div>
        <input type="file" 
          ref={this.props.selectorRef}  
          onChange={this.handleChange} 
          className="hidden"
        />
        <button onClick={()=>
            this.props.selectorRef.current.click()
          }>
          Select file
        </button>
      </div>
    );
  }
}

class App extends React.Component {
  
  constructor(props) {
    super(props);
    this.state = {
      selectorRef : React.createRef(null),
      handleSelectFile : this.handleSelectFile.bind(this),
      uploadedImage: null,
      resultImage: null,
      processingImage: false,
      showabout: false
    };
  }
  
  handleSelectFile(file) {

    var filename = file.name;
    if(filename.endsWith('.png') || filename.endsWith('.jpg') 
      || filename.endsWith('.jpeg'))
      this.setState({uploadedImage: file});
    else
      alert('Accepted formats: png jpg jpeg');
    
  }

  fetchImage = async () => {
    await this.setState({processingImage : true});
    const formData = new FormData();
    formData.append('file', this.state.uploadedImage);
    const res = await fetch('/process',{
      method : 'POST',
      body : formData
    })
    if(!res.ok){
      window.location.reload();
    }
    else{
      if(res.headers.get('error')==='OK'){
        const imageBlob = await res.blob();
        const imageObjectURL = URL.createObjectURL(imageBlob);
        this.setState({resultImage : imageObjectURL});
        await fetch("/delete");
        this.setState({processingImage : false});
      }
      else if(res.headers.get('error')==='File being processed'){
        alert(res.headers.get('error'));
        this.setState({processingImage : true});
      }
      else{
        alert(res.headers.get('error'));
        this.setState({processingImage : false});
      }
    }
  };

  render()
  {
    return (
      <div className="App">
        <div className="ImageBox">
          <img src={this.state.uploadedImage ? URL.createObjectURL(this.state.uploadedImage) : null} alt=""></img>
        </div>

        <div className="Function">

          <h1>Denoise</h1>
          <img src={logo} className="App-logo" alt="logo" />

          <SelectFile 
            selectorRef={this.state.selectorRef}
            onFileChange={this.state.handleSelectFile}
          />

          <button onClick={this.fetchImage}>
            Process
          </button> 
  
          <div className="aboutContent" 
            style={{ display: this.state.showabout ? "block" : "none" }}>
              <div className="aboutContentPanel">
                <div>React + Flask + PyTorch App</div>
                <div>Gaussian noise removal</div>
                <div>For more information</div>
                <div>on the deep learning model, visit:</div>
                <div>https://github.com/nikopj/CDLNet-OJSP</div>
                <div>File should be .png .jpg or .jpeg</div>
                <div>File should be less than 1MB</div>
              </div>
          </div>

          <p className="about" 
            onClick={()=>{this.setState({showabout : !this.state.showabout})}}> 
              about 
          </p>  
        </div>

        <div className="ImageBox">
          <img src={processing} id="processing" 
          style={{ display: this.state.processingImage ? "block" : "none" }} alt="" ></img>
          <img src={this.state.resultImage} 
          style={{ display: this.state.processingImage ? "none" : "block" }} alt=""></img>
        </div>

      </div>
    );
  }
}

export default App;
