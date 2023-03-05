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
      processingImage: null
    };
  }
  
  handleSelectFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    fetch('/upload',{
      method : 'POST',
      body : formData
    })
    this.setState({uploadedImage: URL.createObjectURL(file)});
  }

  fetchImage = async () => {
    this.setState({resultImage : processing});
    const res = await fetch("/process");
    const imageBlob = await res.blob();
    const imageObjectURL = URL.createObjectURL(imageBlob);
    this.setState({resultImage : imageObjectURL});
    fetch("/delete");
  };

  render()
  {
    return (
      <div className="App">

        <div className="ImageBox">
          <img src={this.state.uploadedImage} alt=""></img>
        </div>

        <div className="Function">
          <h1> Denoise </h1>
          <img src={logo} className="App-logo" alt="logo" />

          <SelectFile 
            selectorRef={this.state.selectorRef}
            onFileChange={this.state.handleSelectFile}
          />

          <button onClick={this.fetchImage}>
            Process
          </button>          
        </div>

        <div className="ImageBox">
          <img src={this.state.resultImage} alt=""></img>
        </div>

      </div>
    );
  }
}

export default App;
